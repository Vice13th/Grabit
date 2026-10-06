; GrabIt installer — Inno Setup script (https://jrsoftware.org/isinfo.php)
; Run on Windows, after building dist\GrabIt.exe (see build_installer.md):
;   iscc installer.iss
; Produces GrabIt-Setup-1.0.4.exe — a single branded installer that puts
; GrabIt.exe + Start Menu/Desktop shortcuts on the target machine, all using
; the app's logo as the icon (installer wizard, shortcuts, uninstaller).

#define MyAppName "GrabIt"
#define MyAppVersion "1.0.4"
#define MyAppExeName "GrabIt.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=GrabIt-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
SetupIconFile=grabit\gui\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
; WizardSmallImageFile / WizardImageFile can point at logo.png-derived BMPs
; for a fully branded install wizard, if you want the extra polish:
; WizardSmallImageFile=grabit\gui\assets\logo-small.bmp
; WizardImageFile=grabit\gui\assets\logo-wizard.bmp

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch GrabIt"; Flags: nowait postinstall skipifsilent
