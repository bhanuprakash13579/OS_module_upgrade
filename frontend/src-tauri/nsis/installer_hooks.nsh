; COPS NSIS installer hooks
; Injected into Tauri's generated installer via tauri.conf.json → bundle.windows.nsis.installerHooks
;
; WHY THIS EXISTS:
; python-server.exe is a PyInstaller-built binary and is not code-signed.
; Windows Defender scans it as it is copied into the install directory and
; sometimes quarantines it — the install then fails partway with a message
; naming that file and nothing about why. Excluding the install directory
; BEFORE the copy prevents it.
;
; WHY IT VERIFIES ITSELF:
; Add-MpPreference is refused when Tamper Protection is on, which it is by
; default on Windows 10 and 11. The previous version of this hook discarded the
; result, so the exclusion could fail in complete silence and the installer
; carried on to fail later at the copy — pointing at python-server.exe, which
; is not the problem. It now checks whether the exclusion actually took effect
; and says what to do when it did not.

; ${If} comes from LogicLib and ${FileExists} from FileFunc. Tauri's template
; already includes both, and both carry their own include guards, so naming them
; here is harmless and keeps this file valid on its own.
!include "LogicLib.nsh"
!include "FileFunc.nsh"

!macro NSIS_HOOK_PREINSTALL
  DetailPrint "Configuring Windows Security exclusion for COPS..."

  ; Add the exclusion, then read it back. Asking Defender what it believes is
  ; the only reliable check — the command reports success even where policy
  ; silently discards it.
  nsExec::ExecToStack `powershell.exe -NonInteractive -WindowStyle Hidden -Command "Add-MpPreference -ExclusionPath '$INSTDIR' -ErrorAction SilentlyContinue; if ((Get-MpPreference).ExclusionPath -contains '$INSTDIR') { exit 0 } else { exit 1 }"`
  Pop $0   ; return code
  Pop $1   ; output

  ${If} $0 == 0
    DetailPrint "Windows Security exclusion added for $INSTDIR"
  ${Else}
    ; Not fatal: Defender may still allow the file, and a machine without
    ; Defender at all lands here too. But if the install DOES fail on
    ; python-server.exe, this is why, so say it now rather than leave the
    ; officer with a filename and no explanation.
    DetailPrint "Could not add a Windows Security exclusion (Tamper Protection may be on)."
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
"Windows Security would not accept an exclusion for COPS.$\r$\n$\r$\n\
This is usually Tamper Protection. Installation can continue, and often works \
anyway.$\r$\n$\r$\n\
If it fails with an error naming python-server.exe, Windows Defender has \
quarantined that file. To fix it:$\r$\n$\r$\n\
  1. Open Windows Security, then Virus & threat protection$\r$\n\
  2. Under Protection history, find the blocked item and choose Restore$\r$\n\
  3. Add an exclusion for this folder:$\r$\n\
     $INSTDIR$\r$\n\
  4. Run this installer again$\r$\n$\r$\n\
Continue installing?" \
      IDOK continue_install
    Abort "Installation cancelled."
    continue_install:
  ${EndIf}
!macroend

; ── Post-install: confirm the sidecar actually survived the copy ────────────────
; Defender can quarantine the file AFTER it is written. Checking here turns a
; silent, broken installation — one that installs cleanly and then fails to
; start with no explanation — into a message at the moment it happens.
!macro NSIS_HOOK_POSTINSTALL
  ${IfNot} ${FileExists} "$INSTDIR\python-server.exe"
    MessageBox MB_OK|MB_ICONSTOP \
"COPS installed, but its server component is missing.$\r$\n$\r$\n\
Windows Defender has almost certainly quarantined python-server.exe. The \
application will not start until it is restored.$\r$\n$\r$\n\
  1. Open Windows Security, then Virus & threat protection$\r$\n\
  2. Under Protection history, find the blocked item and choose$\r$\n\
     Allow on device / Restore$\r$\n\
  3. Add an exclusion for:$\r$\n\
     $INSTDIR$\r$\n\
  4. Run this installer again$\r$\n$\r$\n\
The file is part of COPS and is safe; it is flagged because it is not \
code-signed, which is a property of how it is built rather than of what it does."
  ${EndIf}
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
