; GrabIt visible Windows installer.
; Build dist\GrabIt.exe first, then compile with Inno Setup (ISCC.exe).

#define MyAppName "GrabIt"
#define MyAppVersion "1.0.4"
#define MyAppExeName "GrabIt.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=GrabIt-1.0.4-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=grabit\gui\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Tasks]
Name: "startmenu"; Description: "Create a Start Menu shortcut"; GroupDescription: "Shortcuts:"
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "launchafterinstall"; Description: "Launch GrabIt after installation"; GroupDescription: "After installation:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: startmenu
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch GrabIt"; Flags: nowait postinstall skipifsilent; Tasks: launchafterinstall
