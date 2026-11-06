; Inno Setup script: wraps the PyInstaller folder (dist\ChatWithYourDocuments) into one Setup.exe.
; Per-user install (no admin prompt), Start-menu + optional desktop icon, uninstaller.
#define AppName "Chat with your documents"
#define AppExe "ChatWithYourDocuments.exe"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{7E2C1C44-0B1E-4A6B-9C53-2C7A1D0C3E51}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Build, Break, Fix
AppPublisherURL=https://github.com/Berdun/ai-tools
DefaultDirName={localappdata}\Programs\ChatWithYourDocuments
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=ChatWithYourDocuments-Setup-{#AppVersion}
SetupIconFile=app.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\ChatWithYourDocuments\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\samples\handbook.pdf"; DestDir: "{app}\samples"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Start {#AppName} now"; Flags: nowait postinstall skipifsilent
