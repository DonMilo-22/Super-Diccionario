[Setup]
AppName=Word Helper
AppVersion=2.0.0
DefaultDirName={autopf}\Word Helper
DefaultGroupName=Word Helper
OutputDir=installer
OutputBaseFilename=Word-Helper-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\Word Helper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Word Helper"; Filename: "{app}\Word Helper.exe"
Name: "{autodesktop}\Word Helper"; Filename: "{app}\Word Helper.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\Word Helper.exe"; Description: "Abrir Word Helper"; Flags: nowait postinstall skipifsilent
