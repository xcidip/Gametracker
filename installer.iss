; ============================================================
; Inno Setup Script for GameTracker App & Playtime Tracker
; ============================================================

[Setup]
AppId={{C375D62D-0A43-45F9-9611-342882BB17D}
AppName=GameTracker
AppVersion=1.0.0
AppPublisher=Antigravity Team
AppPublisherURL=https://github.com
AppSupportURL=https://github.com
AppUpdatesURL=https://github.com
DefaultDirName={autopf}\GameTracker
DefaultGroupName=GameTracker
AllowNoIcons=yes
LicenseFile=
OutputDir=dist_installer
OutputBaseFilename=GameTracker_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\GameTracker.exe
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\GameTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\GameTracker"; Filename: "{app}\GameTracker.exe"
Name: "{group}\{cm:UninstallProgram,GameTracker}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\GameTracker"; Filename: "{app}\GameTracker.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GameTracker.exe"; Description: "{cm:LaunchProgram,GameTracker}"; Flags: nowait postinstall skipifsilent
