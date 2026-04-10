; COPS NSIS installer hooks
; Injected into Tauri's generated installer via tauri.conf.json → bundle.windows.nsis.installerHooks
;
; WHY THIS EXISTS:
; python-server.exe is a PyInstaller-built binary (unsigned).
; Windows Defender scans and sometimes quarantines it as files are
; being copied to the install directory.  Adding the install directory
; to Defender's exclusion list BEFORE the copy step prevents that.
; The exclusion is machine-scoped (requires the admin rights that the
; NSIS installer already holds) and is cleaned up on uninstall.

; ── Pre-install: add Defender exclusion so python-server.exe is not quarantined ──
!macro NSIS_HOOK_PREINSTALL
  DetailPrint "Configuring Windows Security exclusion for COPS..."
  nsExec::ExecToStack `powershell.exe -NonInteractive -WindowStyle Hidden -Command "Add-MpPreference -ExclusionPath '$INSTDIR' -ErrorAction SilentlyContinue"`
  Pop $0
  Pop $1
!macroend

; ── Post-install: nothing extra needed ───────────────────────────────────────────
!macro NSIS_HOOK_POSTINSTALL
!macroend

; ── Pre-uninstall: nothing extra needed ──────────────────────────────────────────
!macro NSIS_HOOK_PREUNINSTALL
!macroend

; ── Post-uninstall: remove the Defender exclusion we added ───────────────────────
!macro NSIS_HOOK_POSTUNINSTALL
  DetailPrint "Removing Windows Security exclusion for COPS..."
  nsExec::ExecToStack `powershell.exe -NonInteractive -WindowStyle Hidden -Command "Remove-MpPreference -ExclusionPath '$INSTDIR' -ErrorAction SilentlyContinue"`
  Pop $0
  Pop $1
  ; Remove the PyInstaller extraction cache created by the startup speed optimisation.
  ; This is in AppData\Local\COPS\runtime_cache (separate from $INSTDIR).
  DetailPrint "Removing COPS runtime cache..."
  RMDir /r "$LOCALAPPDATA\COPS\runtime_cache"
!macroend
