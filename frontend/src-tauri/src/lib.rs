use std::sync::Mutex;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use tauri::{Manager, Emitter};
#[cfg(not(debug_assertions))]
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandChild;
#[cfg(not(debug_assertions))]
use tauri_plugin_shell::process::CommandEvent;

// ── Windows-only: raw Win32 FFI for focus-safe window show + taskbar fix ─────
// We declare only the handful of API functions we actually need so there is no
// extra crate dependency. All functions live in user32.dll / kernel32.dll which
// are always present on Windows.
#[cfg(target_os = "windows")]
mod win32 {
    use std::ffi::c_void;

    pub type HWND   = *mut c_void;
    pub type LPARAM = isize;
    pub type BOOL   = i32;
    pub type DWORD  = u32;

    pub const GWL_EXSTYLE:      i32 = -20;
    pub const WS_EX_TOOLWINDOW: i32 = 0x0000_0080_u32 as i32;
    pub const WS_EX_APPWINDOW:  i32 = 0x0004_0000_u32 as i32;
    /// Shows without activating — the foreground app keeps focus.
    pub const SW_SHOWNOACTIVATE: i32 = 4;
    pub const TRUE: BOOL = 1;

    #[link(name = "user32")]
    extern "system" {
        pub fn ShowWindow(hwnd: HWND, n_cmd_show: i32) -> BOOL;
        pub fn GetWindowLongW(hwnd: HWND, n_index: i32) -> i32;
        pub fn SetWindowLongW(hwnd: HWND, n_index: i32, dw_new_long: i32) -> i32;
        pub fn GetClassNameW(hwnd: HWND, lp_class_name: *mut u16, n_max_count: i32) -> i32;
        pub fn EnumChildWindows(
            hwnd_parent:  HWND,
            lp_enum_func: Option<unsafe extern "system" fn(HWND, LPARAM) -> BOOL>,
            l_param:      LPARAM,
        ) -> BOOL;
    }
}

// ── Tauri command: show the main window without stealing focus on Windows ─────
// Called by main.tsx instead of window.show() directly. On Windows this uses
// SW_SHOWNOACTIVATE so COPS appears in the taskbar without yanking focus away
// from whatever the user was doing (e.g. Chrome). On other platforms it falls
// back to the normal Tauri show() call.
#[tauri::command]
fn show_main_window(app: tauri::AppHandle) {
    let Some(window) = app.get_webview_window("main") else { return };

    #[cfg(target_os = "windows")]
    {
        if let Ok(hwnd) = window.hwnd() {
            unsafe {
                // Tauri returns HWND as isize; cast via usize to *mut c_void for FFI.
                win32::ShowWindow(hwnd as usize as win32::HWND, win32::SW_SHOWNOACTIVATE);
            }
        }
    }

    #[cfg(not(target_os = "windows"))]
    {
        let _ = window.show();
    }
}

// ── Windows helper: hide WebView2's internal window from the taskbar ──────────
// WebView2 creates a child window with class "Chrome_WidgetWin_1" under the
// Tauri HWND. Windows 11's DWM picks it up as a second thumbnail, causing the
// "double-tab" effect when hovering over the taskbar icon. Setting
// WS_EX_TOOLWINDOW on that child removes it from the taskbar group while
// keeping it fully functional for rendering.
#[cfg(target_os = "windows")]
unsafe extern "system" fn hide_webview2_thumbnail(
    hwnd:   win32::HWND,
    _param: win32::LPARAM,
) -> win32::BOOL {
    let mut buf = [0u16; 256];
    let len = win32::GetClassNameW(hwnd, buf.as_mut_ptr(), buf.len() as i32);
    if len > 0 {
        let class = String::from_utf16_lossy(&buf[..len as usize]);
        if class.starts_with("Chrome_WidgetWin") {
            let ex = win32::GetWindowLongW(hwnd, win32::GWL_EXSTYLE);
            // Add WS_EX_TOOLWINDOW (omit from taskbar grouping)
            // Remove WS_EX_APPWINDOW (forces inclusion — counter-productive here)
            win32::SetWindowLongW(
                hwnd,
                win32::GWL_EXSTYLE,
                (ex | win32::WS_EX_TOOLWINDOW) & !win32::WS_EX_APPWINDOW,
            );
        }
    }
    win32::TRUE
}

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
      let app_data_dir = match app.path().app_local_data_dir() {
        Ok(d) => d,
        Err(e) => {
          eprintln!("[cops] FATAL: cannot resolve app data dir: {e}");
          // Emit so the frontend can show an error rather than spinning forever
          let _ = app.handle().emit("sidecar-startup-failed",
            format!("Cannot determine app data directory: {e}. Try reinstalling COPS."));
          return Ok(());
        }
      };

      // Make sure the directory exists
      if let Err(e) = std::fs::create_dir_all(&app_data_dir) {
        eprintln!("[cops] FATAL: cannot create app data dir {:?}: {e}", app_data_dir);
        let _ = app.handle().emit("sidecar-startup-failed",
          format!("Cannot create app data directory: {e}. Check folder permissions."));
        return Ok(());
      }

      // Create a persistent PyInstaller extraction cache directory.
      // By pointing TEMP/TMP/TMPDIR here we give PyInstaller's bootloader a
      // stable, absolute, writable path.  After the first launch the _MEI<hash>
      // folder already exists at this path and PyInstaller skips extraction
      // entirely — making every subsequent launch significantly faster.
      let runtime_cache = app_data_dir.join("runtime_cache");
      std::fs::create_dir_all(&runtime_cache).ok();
      let runtime_cache_str = runtime_cache.to_string_lossy().into_owned();

      let db_path = app_data_dir.join("cops_br_database.db");

      // On first install: copy the bundled seed DB into app-data dir
      if !db_path.exists() {
        if let Ok(resource_dir) = app.path().resource_dir() {
          let bundled = resource_dir.join("cops_br_database.db");
          if bundled.exists() {
            if let Err(e) = std::fs::copy(&bundled, &db_path) {
              eprintln!("[cops] Warning: could not copy seed database: {e}");
              // Non-fatal — backend will create a fresh DB on first run
            }
          }
        }
      }

      // Normalise to forward slashes so the Python side builds a valid
      // sqlite:///C:/Users/... URL regardless of platform.
      let db_path_str = db_path.to_string_lossy().replace('\\', "/");

      // Register managed state (empty initially; filled by the restart loop below)
      app.manage(PythonSidecar(Mutex::new(None)));
      app.manage(SidecarRestartEnabled(AtomicBool::new(true)));
      app.manage(FastCrashCount(AtomicU32::new(0)));

      // ── Windows: fix WebView2 double-taskbar thumbnail ────────────────────
      // WebView2 creates a "Chrome_WidgetWin_1" child window that Windows 11
      // DWM treats as a second app window, causing two thumbnails when hovering
      // the taskbar icon. We enumerate child windows after a short delay (to let
      // WebView2 finish creating them) and set WS_EX_TOOLWINDOW on any match so
      // they are hidden from the taskbar while still rendering normally.
      #[cfg(target_os = "windows")]
      {
        if let Some(main_win) = app.get_webview_window("main") {
          if let Ok(main_hwnd) = main_win.hwnd() {
            tauri::async_runtime::spawn(async move {
              // Give WebView2 time to create its child windows (~200 ms in practice;
              // 800 ms is a conservative buffer for slow machines / cold starts).
              tokio::time::sleep(std::time::Duration::from_millis(800)).await;
              unsafe {
                win32::EnumChildWindows(
                  main_hwnd as usize as win32::HWND,
                  Some(hide_webview2_thumbnail),
                  0,
                );
              }
            });
          }
        }
      }

      let app_handle = app.handle().clone();
      let db_path_owned = db_path_str;
      let runtime_cache_owned = runtime_cache_str;

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
            .map(|c| c
              .env("COPS_DB_PATH", &db_path_owned)
              // Point PyInstaller's bootloader to our persistent cache dir.
              // Same binary → same _MEI<hash> → no re-extraction after first run.
              .env("TEMP",   &runtime_cache_owned)   // Windows primary
              .env("TMP",    &runtime_cache_owned)   // Windows fallback
              .env("TMPDIR", &runtime_cache_owned)   // Linux / macOS
            )
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
                let error_msg = if cfg!(target_os = "windows") {
                  format!("Cannot start the backend server: {e}. \
                    Windows Defender may have quarantined python-server.exe. \
                    Go to Windows Security → Virus & threat protection → \
                    Protection history, find python-server.exe and click Allow. \
                    Then restart COPS.")
                } else {
                  format!("Cannot start the backend server: {e}. Please check backend/cops_startup.log for reasons.")
                };
                let _ = app_handle.emit("sidecar-startup-failed", error_msg);
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
          if uptime < 60 {
            let crashes = if let Some(c) = app_handle.try_state::<FastCrashCount>() {
              c.0.fetch_add(1, Ordering::SeqCst) + 1
            } else { 1 };
            eprintln!("[cops] Sidecar fast-crash #{crashes} (up for {uptime}s).");
            if crashes >= 4 {
              let error_msg = if cfg!(target_os = "windows") {
                "The backend server crashed on startup. This is often caused by \
                 Windows Defender blocking the server binary. \
                 Please check Windows Security → Virus & threat protection → \
                 Protection history and restore/allow 'python-server.exe'. \
                 Then restart COPS."
              } else {
                "The backend server crashed on startup. Please check the backend/cops_startup.log file for error details."
              };
              let _ = app_handle.emit("sidecar-startup-failed", error_msg);
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
    .invoke_handler(tauri::generate_handler![show_main_window])
    .plugin(tauri_plugin_shell::init())
    .plugin(tauri_plugin_dialog::init())
    .plugin(tauri_plugin_fs::init())
    .plugin(tauri_plugin_updater::Builder::new().build())
    .plugin(tauri_plugin_process::init())
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
