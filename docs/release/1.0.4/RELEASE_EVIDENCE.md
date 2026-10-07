# GrabIt 1.0.4 Windows Release Evidence

## Source
- Repository: Vice13th/Grabit
- Branch: release/1.0.4-windows-packaging
- Commit: a1eb44659b45037818008a38cf609667c6302eff
- Tag: v1.0.4
- Tag target: a1eb44659b45037818008a38cf609667c6302eff

## Build
- Platform: Windows x64
- Python: 3.11.9
- PyInstaller: 6.22.3
- Tests: 19 passed
- EXE: dist\\GrabIt.exe
- EXE size: 50,947,203 bytes
- EXE SHA256: 52489D7DEAFC216723FF8194A87996B08E709F3CB92446DCB31EC85231A2AFE0

## EXE Runtime
- Launch: VERIFIED
- GUI: VERIFIED
- Settings: VERIFIED
- About: VERIFIED
- Navigation: VERIFIED
- Representative download: VERIFIED

## Installer
- Compiler: C:\\Program Files\\Inno Setup 7\\ISCC.exe
- Compiler version: Inno Setup 7.0.2
- Fresh compile: VERIFIED
- Compile exit code: 0
- Compile result: Successful compile (9.422 sec)
- Installer: Output\\GrabIt-1.0.4-Windows-x64-Setup.exe
- Installer size: 52,649,030 bytes
- Replacement installer SHA256: 4B2F552E219FD8BB770BA3462C704ED8DDA6566210632777A485D03166E8A85B
- Replacement compile independently produced the same SHA256 as the lost historical artifact; this is a newly compiled artifact, not a recovered file.

## Installer Provenance
The originally verified installer artifact was:
- Size: 52,649,030 bytes
- SHA256: 4B2F552E219FD8BB770BA3462C704ED8DDA6566210632777A485D03166E8A85B

That exact binary was subsequently lost and could not be recovered from legitimate local storage, Recycle Bin, or available CI artifacts.

A replacement installer was freshly compiled from the immutable v1.0.4 release tag using Inno Setup 7.0.2.

The replacement installer was independently hashed and produced the same SHA256 value as the lost historical artifact. No historical binary was recovered or substituted.

## Replacement Installer
- Compiler: Inno Setup
- Version: 7.0.2
- Fresh compile: VERIFIED
- Compile exit code: 0
- Compile result: Successful compile (9.422 sec)
- Installer SHA256: 4B2F552E219FD8BB770BA3462C704ED8DDA6566210632777A485D03166E8A85B
- Installer size: 52,649,030 bytes
- Embedded GrabIt.exe SHA256: 52489D7DEAFC216723FF8194A87996B08E709F3CB92446DCB31EC85231A2AFE0
- Embedded EXE matches verified release EXE: VERIFIED
- Embedded EXE version: 1.0.4.0
- Embedded EXE product: GrabIt
- Embedded EXE original filename: GrabIt.exe
- Installer payload inspection: VERIFIED with innounp 2.71.1
- Detected installer format: Inno Setup 7.0.0 (Unicode), setup data 7.0.0.3
- Extracted payload size: 50,947,203 bytes

## Installation
Historical installation evidence below belongs to the previously verified installer artifact. The replacement installer was not installed or runtime-tested.

- Interactive install: VERIFIED (historical installer)
- Install location: C:\\Program Files\\GrabIt
- Start Menu shortcut: VERIFIED (historical installer)
- Desktop shortcut: VERIFIED (historical installer)
- Installed app launch: VERIFIED (historical installer)
- Installed app download: VERIFIED (historical installer)

## Uninstall
Historical uninstall evidence below belongs to the previously verified installer artifact.

- Normal uninstall: VERIFIED (historical installer)
- Files removed: VERIFIED (historical installer)
- Shortcuts removed: VERIFIED (historical installer)
- Registry uninstall entry removed: VERIFIED (historical installer)
- Process removed: VERIFIED (historical installer)

## Screenshots
Historical screenshots below belong to the previously verified installer artifact.
- Main: VERIFIED (historical installer)
- Installer: VERIFIED (historical installer)
- Installed: VERIFIED (historical installer)

## Final Gate
- BUILD: VERIFIED
- EXE: VERIFIED
- RUNTIME: VERIFIED
- DOWNLOAD: VERIFIED
- REPLACEMENT INSTALLER BUILD: VERIFIED
- REPLACEMENT INSTALLER CONTENTS: VERIFIED
- EMBEDDED EXE HASH MATCH: VERIFIED
- HISTORICAL INSTALL: VERIFIED
- HISTORICAL INSTALLED RUNTIME: VERIFIED
- HISTORICAL SHORTCUTS: VERIFIED
- HISTORICAL UNINSTALL: VERIFIED
- HISTORICAL SCREENSHOTS: VERIFIED
- EVIDENCE: VERIFIED

## VERDICT
READY
