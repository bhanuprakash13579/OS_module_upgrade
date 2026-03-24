use std::sync::Mutex;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use tauri::Manager;
#[cfg(not(debug_assertions))]
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandChild;
#[cfg(not(debug_assertions))]
use tauri_plugin_shell::process::CommandEvent;

/// Holds the python-server child process (updated on every restart).
struct PythonSidecar(Mutex<Option<CommandChild>>);

/// Set to false on app shutdown so the restart loop stops looping.
struct SidecarRestartEnabled(AtomicBool);

/// Counts consecutive fast crashes (sidecar exits within a few seconds of starting).
/// Emits a "sidecar-startup-failed" event to the frontend after too many.
struct FastCrashCount(AtomicU32);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  // Fix blank white page on Linux/Wayland:
  // WebKitGTK 2.48+ DMA-BUF compositor breaks rendering under Wayland/GTK3.
  // Force X11 backend (via XWayland) and disable the DMA-BUF renderer path.
  // The #[cfg] guard ensures this is a no-op on Windows and macOS.
  #[cfg(target_os = "linux")]
  {
    std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    std::env::set_var("GDK_BACKEND", "x11");
  }

  tauri::Builder::default()
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      // Resolve the user's app-data directory for this machine
      // e.g. C:\Users\<user>\AppData\Local\COPS  (Windows)
      //      ~/.local/share/COPS                 (Linux)
      let app_data_dir = app
        .path()
        .app_local_data_dir()
        .expect("could not resolve app data dir");

      // Make sure the directory exists
      std::fs::create_dir_all(&app_data_dir)
        .expect("could not create app data dir");

      let db_path = app_data_dir.join("cops_br_database.db");

      // On first install: copy the bundled seed DB into app-data dir
      if !db_path.exists() {
        let bundled = app
          .path()
          .resource_dir()
          .expect("could not resolve resource dir")
          .join("cops_br_database.db");
        if bundled.exists() {
          std::fs::copy(&bundled, &db_path)
            .expect("could not copy seed database");
        }
      }

      // Normalise to forward slashes so the Python side builds a valid
      // sqlite:///C:/Users/... URL regardless of platform.
      let db_path_str = db_path.to_string_lossy().replace('\\', "/");

      // Register managed state (empty initially; filled by the restart loop below)
      app.manage(PythonSidecar(Mutex::new(None)));
      app.manage(SidecarRestartEnabled(AtomicBool::new(true)));
      app.manage(FastCrashCount(AtomicU32::new(0)));

      let app_handle = app.handle().clone();
      let db_path_owned = db_path_str;

      // Sidecar supervisor loop — spawns the Python server and auto-restarts it
      // if it crashes unexpectedly. Stops cleanly when the app window is closed.
      //
      // In debug/dev builds the sidecar is NOT started — run the backend manually:
      //   cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000
      #[cfg(debug_assertions)]
      {
        eprintln!("[cops] DEV MODE — skipping sidecar. Start uvicorn manually on :8000.");
        let _ = (db_path_owned, app_handle); // suppress unused warnings
      }
      #[cfg(not(debug_assertions))]
      tauri::async_runtime::spawn(async move {
        loop {
          // Check shutdown flag before each spawn attempt
          if let Some(flag) = app_handle.try_state::<SidecarRestartEnabled>() {
            if !flag.0.load(Ordering::SeqCst) {
              break;
            }
          }

          let sidecar_cmd = match app_handle
            .shell()
            .sidecar("python-server")
            .map(|c| c.env("COPS_DB_PATH", &db_path_owned))
          {
            Ok(c) => c,
            Err(e) => {
              eprintln!("[cops] Failed to build sidecar command: {e}");
              let _ = app_handle.emit("sidecar-startup-failed",
                format!("Cannot locate python-server binary: {e}. Try reinstalling the app."));
              break;
            }
          };

          let (mut rx, child) = match sidecar_cmd.spawn() {
            Ok(r) => r,
            Err(e) => {
              eprintln!("[cops] Failed to spawn python sidecar: {e}. Retrying in 5s...");
              // Spawn failures (binary not found, Defender quarantine, etc.)
              // also count toward the crash threshold so the frontend gets notified.
              let spawn_fails = if let Some(c) = app_handle.try_state::<FastCrashCount>() {
                c.0.fetch_add(1, Ordering::SeqCst) + 1
              } else { 1 };
              if spawn_fails >= 4 {
                let _ = app_handle.emit("sidecar-startup-failed",
                  format!("Cannot start the backend server: {e}. \
                    Windows Defender may have quarantined python-server.exe. \
                    Go to Windows Security → Virus & threat protection → \
                    Protection history, find python-server.exe and click Allow. \
                    Then restart COPS."));
                if let Some(c) = app_handle.try_state::<FastCrashCount>() {
                  c.0.store(0, Ordering::SeqCst);
                }
              }
              tokio::time::sleep(std::time::Duration::from_secs(5)).await;
              continue;
            }
          };

          eprintln!("[cops] Python server started.");
          let spawn_time = std::time::Instant::now();

          // Store child so on_window_event can kill it on shutdown
          if let Some(state) = app_handle.try_state::<PythonSidecar>() {
            if let Ok(mut guard) = state.0.lock() {
              *guard = Some(child);
            }
          }

          // Stream sidecar stdout/stderr to the Tauri console until termination
          while let Some(event) = rx.recv().await {
            match event {
              CommandEvent::Stdout(line) => {
                println!("[server] {}", String::from_utf8_lossy(&line));
              }
              CommandEvent::Stderr(line) => {
                eprintln!("[server] {}", String::from_utf8_lossy(&line));
              }
              _ => {}
            }
          }

          // Process terminated — clear stored child handle
          if let Some(state) = app_handle.try_state::<PythonSidecar>() {
            if let Ok(mut guard) = state.0.lock() {
              *guard = None;
            }
          }

          // Re-check shutdown flag: if the window was closed, don't restart
          if let Some(flag) = app_handle.try_state::<SidecarRestartEnabled>() {
            if !flag.0.load(Ordering::SeqCst) {
              eprintln!("[cops] App is shutting down — not restarting sidecar.");
              break;
            }
          }

          // Fast-crash detection: if the sidecar exits within 5 seconds of
          // starting, count it. After 4 consecutive fast crashes, tell the
          // frontend so it can show an actionable error instead of spinning forever.
          let uptime = spawn_time.elapsed().as_secs();
          if uptime < 5 {
            let crashes = if let Some(c) = app_handle.try_state::<FastCrashCount>() {
              c.0.fetch_add(1, Ordering::SeqCst) + 1
            } else { 1 };
            eprintln!("[cops] Sidecar fast-crash #{crashes} (up for {uptime}s).");
            if crashes >= 4 {
              let _ = app_handle.emit("sidecar-startup-failed",
                "The backend server crashed on startup. This is often caused by \
                 Windows Defender blocking the server binary. \
                 Please check Windows Security → Virus & threat protection → \
                 Protection history and restore/allow 'python-server.exe'. \
                 Then restart COPS.");
              // Keep the restart loop running in case the user fixes it
              if let Some(c) = app_handle.try_state::<FastCrashCount>() {
                c.0.store(0, Ordering::SeqCst); // reset so we alert again after another 4
              }
            }
          } else {
            // Sidecar ran normally for a while — reset the fast-crash counter
            if let Some(c) = app_handle.try_state::<FastCrashCount>() {
              c.0.store(0, Ordering::SeqCst);
            }
          }

          eprintln!("[cops] Python server stopped unexpectedly. Restarting in 2s...");
          tokio::time::sleep(std::time::Duration::from_secs(2)).await;
        }
      }); // end #[cfg(not(debug_assertions))] spawn

      Ok(())
    })
    // On window close: disable restart flag, then kill the sidecar
    .on_window_event(|window, event| {
      if let tauri::WindowEvent::Destroyed = event {
        // Signal the supervisor loop to stop restarting
        if let Some(flag) = window.try_state::<SidecarRestartEnabled>() {
          flag.0.store(false, Ordering::SeqCst);
        }
        // Kill the running sidecar immediately
        if let Some(state) = window.try_state::<PythonSidecar>() {
          if let Ok(mut guard) = state.0.lock() {
            if let Some(child) = guard.take() {
              let _ = child.kill();
            }
          }
        }
      }
    })
    .plugin(tauri_plugin_shell::init())
    .plugin(tauri_plugin_dialog::init())
    .plugin(tauri_plugin_fs::init())
    .plugin(tauri_plugin_updater::Builder::new().build())
    .plugin(tauri_plugin_process::init())
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
