; ###########################################################################
; Inno Setup script for the Fishbowl Invoice Tool.
;
; Produces a per-user, no-UAC installer (FishbowlInvoiceTool_Setup.exe) from
; the release payload that scripts/package_release.sh writes to
; release/FishbowlInvoiceTool/. Designed so that UPGRADES replace the program
; files (exe + user guide) while PRESERVING the customer's edited Configs/ and
; any invoices they have dropped into Invoices/.
;
; The app (see source/constants.py) reads/writes logs/, data/, Configs/ and
; Invoices/ RELATIVE TO ITS OWN EXE, so it is installed per-user into a
; writable location ({localappdata}\Programs) rather than Program Files.
;
; Build (run from the repo root, after building the release payload):
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DAppVersion=3.1.2 scripts\installer.iss
;
; AppVersion is passed in via /D so source/constants.py stays the single source
; of truth; the #ifndef below provides a fallback for a bare manual compile.
; ###########################################################################

#define AppName "Fishbowl Invoice Tool"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppExeName "AutoInvoiceProc.exe"
#define Publisher "Hammond Software"

; Release payload produced by scripts/package_release.sh, relative to this .iss.
#define SourceRoot "..\release\FishbowlInvoiceTool"

[Setup]
; A stable AppId is what lets Inno recognize an existing install and upgrade it
; in place. Do NOT change this GUID across versions.
AppId={{4E1C7A2F-9B3D-4F6A-8C21-5D9E0B7A1F34}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#Publisher}
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#Publisher}
VersionInfoDescription={#AppName} Setup

; Per-user install, no admin prompt. {autopf} under lowest privileges resolves
; to %LOCALAPPDATA%\Programs, which the app can freely write into at runtime.
PrivilegesRequired=lowest
DefaultDirName={autopf}\FishbowlInvoiceTool
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Force close applications Restart Manager cannot shut down gracefully. This is
; what makes the in-app "Update and Restart" work: the running app launches this
; installer and then exits, but Restart Manager scans within a few hundred ms and
; asks the app to close by posting to its window. A PyInstaller onefile build has
; two processes -- the bootloader and its child -- and the bootloader owns no
; window, so it never answers. Setup then waits out its 30-second timeout, reports
; "Some applications could not be shut down", and because the updater passes
; /SUPPRESSMSGBOXES the Abort/Retry/Ignore prompt defaults to Abort: the upgrade
; silently rolls back and the user is left on the old version. Without a window to
; close, no delay on the app's side fixes this -- Setup has to terminate it.
CloseApplications=force

WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes

OutputDir=..\release
OutputBaseFilename=FishbowlInvoiceTool_Setup
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Program files: always replaced on upgrade.
Source: "{#SourceRoot}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceRoot}\USER_GUIDE.txt"; DestDir: "{app}"; Flags: ignoreversion
; Patch notes: ignoreversion like the rest of the program files, and deliberately
; NOT onlyifdoesntexist/uninsneveruninstall like the Configs/Invoices entries below.
; Those flags exist to protect the customer's own data; this is app content that MUST
; be replaced on upgrade, or the app would announce an update by showing the previous
; release's notes.
Source: "{#SourceRoot}\PATCH_NOTES.md"; DestDir: "{app}"; Flags: ignoreversion
; Config files: ship defaults on a clean install, but never overwrite a
; customer's edits on upgrade (onlyifdoesntexist) and never delete on
; uninstall (uninsneveruninstall) -- this is the "preserveexisting" behavior.
Source: "{#SourceRoot}\Configs\*"; DestDir: "{app}\Configs"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs
; Invoices: preserve any the customer has added; tolerate an empty/missing
; source folder (package_release.sh only populates it when run with `true`).
Source: "{#SourceRoot}\Invoices\*"; DestDir: "{app}\Invoices"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs skipifsourcedoesntexist

[Dirs]
; Guarantee the app's writable folders exist even when shipped empty, and keep
; the data-bearing ones on uninstall.
Name: "{app}\logs"
Name: "{app}\data"
Name: "{app}\Configs"; Flags: uninsneveruninstall
Name: "{app}\Invoices"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\User Guide"; Filename: "{app}\USER_GUIDE.txt"
Name: "{group}\What's New"; Filename: "{app}\PATCH_NOTES.md"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Interactive install: offer the usual "launch now" checkbox on the final page.
; skipifsilent keeps a scripted silent deployment from springing a window open.
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; In-app update: the running application launches this installer silently and then
; exits so its executable can be replaced, so nothing above would bring it back.
; Gated on the /RELAUNCH=1 switch the updater passes (see WantsRelaunch below) so
; only that route relaunches, never a hand-run silent install.
Filename: "{app}\{#AppExeName}"; Flags: nowait; Check: WantsRelaunch

[Code]
// Clears one variable from Setup's own environment. Declared against the Win32
// API because Pascal Script has no built-in way to unset a variable; passing an
// empty value deletes it, which is what CMD's "set NAME=" does underneath.
function SetEnvVar(lpName: String; lpValue: String): Boolean;
  external 'SetEnvironmentVariableW@kernel32.dll stdcall';

// Drops the PyInstaller bootloader variables Setup inherited from the app that
// started it, so the relaunched app does not.
//
// The app is a PyInstaller onefile build, so its environment carries _PYI_*
// variables describing the extracted bundle. It launches this installer as a
// child process, which inherits them, and the [Run] relaunch below would pass
// them on again. Since PyInstaller 6.22.1 a starting app that sees them assumes
// it is a worker sub-process of a onefile parent and requires its parent process
// to be the same executable -- here it is Setup, so it refuses to start with
// "Security validation failure: parent process has different executable". An
// in-place upgrade keeps the same path, so nothing else tips it off.
//
// Called from InitializeSetup so it applies to everything Setup spawns.
procedure ClearInheritedPyInstallerEnv;
begin
  SetEnvVar('_PYI_ARCHIVE_FILE', '');
  SetEnvVar('_PYI_APPLICATION_HOME_DIR', '');
  SetEnvVar('_PYI_PARENT_PROCESS_LEVEL', '');
  SetEnvVar('_MEIPASS2', '');
end;

function InitializeSetup: Boolean;
begin
  ClearInheritedPyInstallerEnv;
  Result := True;
end;

// True when the installer was started by the application's own updater, which
// passes /RELAUNCH=1. The param constant below expands to the switch's value, or
// to 0 when it was not passed at all.
//
// These are // comments rather than Pascal's { } form deliberately: a brace
// comment does not nest, so the closing brace of a {param:...} constant written
// inside one ends the comment early and the rest of it is compiled as code.
function WantsRelaunch: Boolean;
begin
  Result := ExpandConstant('{param:relaunch|0}') = '1';
end;
