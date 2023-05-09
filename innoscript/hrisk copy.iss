[Setup]
AppName=H-RISK (with NoiseModelling)
AppVersion=0.0.0900
AppPublisher=Junta Tagusari
AppPublisherURL=https://gitlab.com/jtagusari/hrisk-qgis/
DefaultDirName={pf}\HRISK
DefaultGroupName=H-RISK (with NoiseModelling)
OutputDir=.
Compression=none
Uninstallable=yes

; [Files]
; Source: "https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_windows-x64_bin.zip"; DestDir: "{pf}\java\jdk-11.0.2"; Flags: external; Check: JavaFolderExists
; Source: "https://github.com/Universite-Gustave-Eiffel/NoiseModelling/releases/download/v4.0.4/NoiseModelling_without_gui.zip"; DestDir: "{pf}\NoiseModelling"; Flags: external; Check: NoiseModellingFolderExists
; Source: "..\*"; DestDir: "{userappdata}\QGIS\QGIS3\profiles\default\python\plugins\hrisk"; Flags: recursesubdirs createallsubdirs

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\QGIS\QGIS3\profiles\default\python\plugins\hrisk"
Type: filesandordirs; Name: "{pf}\java\jdk-11.0.2"
Type: filesandordirs; Name: "{pf}\NoiseModelling"
Type: env; Name: "JAVA_FOR_NOISEMODELLING"
Type: env; Name: "NOISEMODELLING_HOME"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"


[CustomMessages]
english.components_title=Select components
japanese.components_title=インストールする項目の選択
english.components_message=Select the components to install.
japanese.components_message=インストールする項目を指定してください。


english.Java_title=Java Installation
japanese.Java_title=Javaのインストール
english.Java_message=Select the installation directory for Java:
japanese.Java_message=Javaのインストール先を指定してください：

english.NoiseModelling_title=NoiseModelling Installation
japanese.NoiseModelling_title=NoiseModellingのインストール
english.NoiseModelling_message=Select the installation directory for NoiseModelling:
japanese.NoiseModelling_message=NoiseModellingのインストール先を指定してください：

english.HRISK_title=HRISK Installation
japanese.HRISK_title=HRISKのインストール
english.HRISK_message=Select the installation directory for H-RISK (it must be QGIS's plugin path):
japanese.HRISK_message=H-RISKのインストール先を指定してください（QGISのプラグインパスと一致している必要があります）：

[Code]
var
  JavaPathPage: TInputDirWizardPage;
  NoiseModellingPathPage: TInputDirWizardPage;
  DownloadPage: TDownloadWizardPage;

procedure InitializeWizard;
begin
  ComponentsPage := CreateInputOptionPage(wpWelcome, 'Select Components', 'Select the components to install', '');
  ComponentsPage.Add('java','Java', "Java");
  ComponentsPage.Add('noisemodelling','NoiseModelling', 'NoiseModelling');
  ComponentsPage.Add('hrisk','H-RISK', 'H-RISK');

  JavaPathPage := CreateInputDirPage(wpSelectComponents, Java_title, Java_message, '{pf}\java\jdk-11.0.2', False, False);
  JavaPathPage.Add('JAVA_FOR_NOISEMODELLING');
  
  NoiseModellingPathPage := CreateInputDirPage(wpSelectComponents, NoiseModelling_title, NoiseModelling_message, '{pf}\NoiseModelling', False, False);
  NoiseModellingPathPage.Add('NOISEMODELLING_HOME');

  HriskPathPage := CreateInputDirPage(wpSelectComponents, Hrisk_title, Hrisk_message, '{userappdata}\QGIS\QGIS3\profiles\default\python\plugins\hrisk', False, False);
  
  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), @OnDownloadProgress);
end;

procedure ExtractZip(const ZipFile, TargetDir: string);
var
  Shell: Variant;
  Source: Variant;
begin
  Shell := CreateOleObject('Shell.Application');
  Source := Shell.NameSpace(ZipFile);
  Shell.NameSpace(TargetDir).CopyHere(Source.Items, 20);
end;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  if Progress = ProgressMax then
    Log(Format('Successfully downloaded file to {tmp}: %s', [FileName]));
  Result := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  if CurPageID = wpReady then begin
    DownloadPage.Clear;
    if IsComponentSelected('java') then
      DownloadPage.Add('https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_windows-x64_bin.zip', 'openjdk-11.0.2.zip', '');
    if IsComponentSelected('noisemodelling') then
      DownloadPage.Add('https://github.com/Universite-Gustave-Eiffel/NoiseModelling/releases/download/v4.0.4/NoiseModelling_without_gui.zip', 'NoiseModelling.zip', '');
    DownloadPage.Show;
    try
      try
        DownloadPage.Download; // This downloads the files to {tmp}

        if IsComponentSelected('java') then
          JavaPath := JavaPathPage.Values[0];
          ExtractZip(ExpandConstant('{tmp}\openjdk-11.0.2.zip'), JavaPath);

        if IsComponentSelected('noisemodelling') then
          NoiseModellingPath := NoiseModellingPathPage.Values[0];
          ExtractZip(ExpandConstant('{tmp}\NoiseModelling.zip'), NoiseModellingPath);

        Result := True;
      except
        if DownloadPage.AbortedByUser then
          Log('Aborted by user.')
        else
          SuppressibleMsgBox(AddPeriod(GetExceptionMessage), mbCriticalError, MB_OK, IDOK);
        Result := False;
      end;
    finally
      DownloadPage.Hide;
    end;
  end else
    Result := True;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;

  if PageID = JavaPathPage.ID then
    Result := not IsComponentSelected('java')
  else if PageID = NoiseModellingPathPage.ID then
    Result := not IsComponentSelected('noisemodelling')
  else if PageID = HriskPathPage.ID then
    Result := not IsComponentSelected('hrisk');
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = JavaPathPage.ID then begin
    if ShouldSkipPage(JavaPathPage.ID) then
      WizardForm.NextButton.Click;
  end else if CurPageID = NoiseModellingPathPage.ID then begin
    if ShouldSkipPage(NoiseModellingPathPage.ID) then
      WizardForm.NextButton.Click;
  end else if CurPageID = HriskPathPage.ID then begin
    if ShouldSkipPage(HriskPathPage.ID) then
      WizardForm.NextButton.Click;
  end;
end;