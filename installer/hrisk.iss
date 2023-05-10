[Setup]
AppName=H-RISK (with NoiseModelling)
AppVersion=0.0.1
AppPublisher=Junta Tagusari
AppPublisherURL=https://gitlab.com/jtagusari/hrisk-qgis/
OutputDir=.
OutputBaseFilename=hrisk-setup
Compression=none
DisableDirPage=yes
DefaultDirName={commonpf64}\H-RISK\withNoiseModelling
Uninstallable=no
UninstallFilesDir={app}\uninst
ArchitecturesInstallIn64BitMode=x64 ia64 arm64
ChangesEnvironment=yes
PrivilegesRequired=admin

[Files]
Source: "..\*"; DestDir: "{tmp}\hrisk"; Flags: ignoreversion dontcopy;
Source: "..\i18n\*"; DestDir: "{tmp}\hrisk\i18n"; Flags: recursesubdirs dontcopy;
Source: "..\noisemodelling/*"; DestDir: "{tmp}\hrisk\noisemodelling"; Flags: recursesubdirs dontcopy;
Source: "..\installer\unzip.exe"; DestDir: "{app}"; Flags: ignoreversion dontcopy;


[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "infobefore-en.txt"
Name: "ja"; MessagesFile: "compiler:Languages\Japanese.isl"; InfoBeforeFile: "infobefore-ja.txt"

[CustomMessages]
en.selectdir_title=%1 Installation
ja.selectdir_title=%1 のインストール
en.selectdir_desc=Where should %1 be installed?
ja.selectdir_desc=%1 のインストール先を指定してください
en.selectdir_label=Setup will install %1 into the following folder.
ja.selectdir_label=%1 をインストールするフォルダを指定して，「次へ」をクリックしてください。
en.setreg_msg=Do you want to set the environment variable %1 to %2? If there is an existing setting, it will be overwritten.
ja.setreg_msg=環境変数 %1 を %2 に設定しますか？既存の設定がある場合には上書きします。
en.setreg_info=Setting the environment variable %1 to %2 is required to run %3. Please set it if necessary.
ja.setreg_info=H-RISKの実行には環境変数 %1 の設定が必要です。必要に応じて設定してください。
en.unzip_err=Failed to unzip. Exit code: %1
ja.unzip_err=解凍に失敗しました。終了コード：%1

[Code]
// 変数の宣言
const
  Java_name = 'Java (for NoiseModelling)';
  Java_dir_default = '{commonpf64}\Java';
  Java_env = 'JAVA_FOR_NOISEMODELLING';
  Java_URL = 'https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_windows-x64_bin.zip';
  NoiseModelling_name = 'NoiseModelling';
  NoiseModelling_dir_default = '{commonpf64}\NoiseModelling';
  NoiseModelling_env='NOISEMODELLING_HOME';
  NoiseModelling_URL = 'https://github.com/Universite-Gustave-Eiffel/NoiseModelling/releases/download/v4.0.4/NoiseModelling_without_gui.zip';
  Hrisk_name = 'H-RISK';
  Hrisk_dir_default = '{userappdata}\QGIS\QGIS3\profiles\default\python\plugins\hrisk';
var
  components_page: TInputOptionWizardPage;
  Java_path_page: TInputDirWizardPage;
  NoiseModelling_path_page: TInputDirWizardPage;
  Hrisk_path_page: TInputDirWizardPage;
  download_page: TDownloadWizardPage;


// ダウンロードの進捗を表示する関数
function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  if Progress = ProgressMax then
    Log(Format('Successfully downloaded file to {tmp}: %s', [FileName]));
  Result := True;
end;

// フォルダごとコピーする関数
// by @tohshima (https://qiita.com/tohshima/items/156679386f6486c4d278)
procedure XCopyFile(sourcePath, destPath: String);
var
  FindRec: TFindRec;
begin

  if not DirExists(destPath) then
  begin
    if not CreateDir(destPath) then
    begin
      MsgBox('Failed to create folder.', mbError, MB_OK);
      Exit;
    end;
  end;

  if FindFirst(sourcePath+'\*', FindRec) then begin
    try
      repeat
        // フォルダ自身と親フォルダは処理しない
        if (FindRec.Name<>'.') and (FindRec.Name<>'..') then 
        begin
          // ファイルのとき
          if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY = 0 then begin
            FileCopy(sourcePath + '\' + FindRec.Name, destPath + '\' + FindRec.Name, False);
          // ディレクトリのとき
          end else begin
            CreateDir(destPath + '\' + FindRec.Name);
            XCopyFile(sourcePath + '\' + FindRec.Name, destPath + '\' + FindRec.Name);
          end;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

// ウィザードの初期化プロシージャ
procedure InitializeWizard;
var
  after_id: Integer;
begin

  // インストールコンポーネントの選択画面
  after_id := wpInfoBefore;
  components_page := CreateInputOptionPage(
    after_id, 
    setupMessage(msgWizardSelectComponents), 
    setupMessage(msgSelectComponentsDesc), 
    setupMessage(msgSelectComponentsLabel2), 
    False, False);
  components_page.Add(Java_name);
  components_page.Add(NoiseModelling_name);
  components_page.Add(Hrisk_name);
  components_page.Values[0] := True;
  components_page.Values[1] := True;
  components_page.Values[2] := False;
  after_id := components_page.ID;

  // Javaインストール先の設定画面
  Java_path_page := CreateInputDirPage(
    after_id, 
    ExpandConstant('{cm:selectdir_title,' + Java_name + '}'), 
    ExpandConstant('{cm:selectdir_desc, ' + Java_name + '}'), 
    ExpandConstant('{cm:selectdir_label,' + Java_name + '}'),
    False, '');
  Java_path_page.Add('');
  Java_path_page.Values[0] := ExpandConstant(Java_dir_default);
  after_id := Java_path_page.ID;
  
  // NoiseModellingインストール先の設定画面
  NoiseModelling_path_page := CreateInputDirPage(
    after_id, 
    ExpandConstant('{cm:selectdir_title, ' + NoiseModelling_name + '}'), 
    ExpandConstant('{cm:selectdir_desc,  ' + NoiseModelling_name + '}'), 
    ExpandConstant('{cm:selectdir_label, ' + NoiseModelling_name + '}'),
    False, '');
  NoiseModelling_path_page.Add('');
  NoiseModelling_path_page.Values[0] := ExpandConstant(NoiseModelling_dir_default);
  after_id := NoiseModelling_path_page.ID;

  // H-RISKインストール先の設定画面
  Hrisk_path_page := CreateInputDirPage(
    after_id, 
    ExpandConstant('{cm:selectdir_title, '+ Hrisk_name + '}'), 
    ExpandConstant('{cm:selectdir_desc,  '+ Hrisk_name + '}'), 
    ExpandConstant('{cm:selectdir_label, '+ Hrisk_name + '}'),
    False, '');
  Hrisk_path_page.Add('');
  Hrisk_path_page.Values[0] := ExpandConstant(Hrisk_dir_default);
  
  // ダウンロードウィザード
  download_page := CreateDownloadPage(
    SetupMessage(msgWizardPreparing), 
    SetupMessage(msgPreparingDesc), 
    @OnDownloadProgress
    );
end;

// 環境変数を設定するプロシージャ
procedure SetEnvironmentVariable(const Name, Value: string);
begin
  if MsgBox(
    ExpandConstant('{cm:setreg_msg, ' + Name + ',' + Value +'}'), 
    mbConfirmation, MB_YESNO
    ) = IDYES then
  begin
    RegWriteStringValue(
      HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
      Name, Value
    );
  end
  else begin
    MsgBox(ExpandConstant('{cm:setreg_info, ' + Name +'}'), mbInformation, MB_OK)
  end;
end;

// zipファイルを解凍するプロシージャ
procedure ExtractZip(ZipFile, TargetDir: string);
var
  ResultCode: Integer;
begin
  if not DirExists(TargetDir) then
  begin
    if not CreateDir(TargetDir) then
    begin
      MsgBox('Failed to create folder.', mbError, MB_OK);
      Exit;
    end;
  end;

  if Exec(
    ExpandConstant('{tmp}\unzip.exe'),
    '-o "' + ZipFile + '" -d "' + TargetDir + '"',
    '', SW_SHOW, ewWaitUntilTerminated, ResultCode
  ) then
  begin
    Log(Format('Successfully extracted {tmp}: %s', [ZipFile]));
  end else begin
    MsgBox(ExpandConstant('{cm:unzip_err,'+InttoStr(ResultCode)+'}'), mbError, MB_OK);
  end;
end;


// 「次へ」ボタンが押された時の処理
function NextButtonClick(CurPageID: Integer): Boolean;
begin

  // 「インストールの準備完了」画面で「次へ」を押したときの処理
  if CurPageID = wpReady then 
  begin

    // ファイルのダウンロード
    download_page.Clear;
    if components_page.Values[0] then
      download_page.Add(Java_URL, 'openjdk.zip', '');
    if components_page.Values[1] then
      download_page.Add(NoiseModelling_URL, 'NoiseModelling.zip', '');
    download_page.Show;

    // ダウンロードの実行
    try
      download_page.Download; // {tmp}にダウンロードされる
      Result := True;
    except
      if download_page.AbortedByUser then
        Log('Aborted by user.')
      else
        SuppressibleMsgBox(AddPeriod(GetExceptionMessage), mbCriticalError, MB_OK, IDOK);
      Result := False;
    finally
      download_page.Hide;
    end;

    // ファイルの展開・環境変数の設定
    if Result = True then
    begin
      ExtractTemporaryFile('unzip.exe'); // 解凍用のexe

      // Javaの展開・環境変数の設定
      if components_page.Values[0] then
      begin
        ExtractZip(ExpandConstant('{tmp}\openjdk.zip'), Java_path_page.Values[0])
        SetEnvironmentVariable(Java_env, Java_path_page.Values[0] + '\jdk-11.0.2');
      end;

      // NoiseModellingの展開・環境変数の設定
      if components_page.Values[1] then
      begin
        ExtractZip(ExpandConstant('{tmp}\NoiseModelling.zip'), NoiseModelling_path_page.Values[0])
        SetEnvironmentVariable(NoiseModelling_env, NoiseModelling_path_page.Values[0])
      end;

      // H-RISKの展開
      if components_page.Values[2] then      
      begin
        ExtractTemporaryFiles('{tmp}\hrisk\*');
        XCopyFile(ExpandConstant('{tmp}\hrisk'), Hrisk_path_page.Values[0]);
      end;
      
    end;
  end;

  // それ以外の場合にはTrueを返す
  Result := True;
end;


// ページをスキップするかの判定                                      
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;

  if PageID = Java_path_page.ID then
    Result := not components_page.Values[0]
  else if PageID = NoiseModelling_path_page.ID then
    Result := not components_page.Values[1]
  else if PageID = Hrisk_path_page.ID then
    Result := not components_page.Values[2]
end;
