[日本語版 README はこちら](/README-ja.md)

## このソフトウェアについて

騒音予測・健康リスク推定のためのQGISプラグインです。
NoiseModellingによる騒音予測を実装しています。

## 機能

- OpenStreetMap、Shuttle Radar Topography Mission、Vector Tiles（国土地理院提供）からジオメトリを取得する
- NoiseModellingを使用して騒音レベルを予測する
- 予測された騒音レベルと、欧州地域における環境騒音ガイドライン（WHO欧州地域事務局）に示された暴露-反応関係に基づいて、健康リスクを推定する

## クレジット

- このサービスは、政府統計総合窓口(e-Stat)のAPI機能を使用していますが、サービスの内容は国によって保証されたものではありません。

## 参照ウェブサイト

- NoiseModelling (https://noise-planet.org/noisemodelling.html)
- QGIS (https://qgis.org/)
- 国土地理院ベクトルタイル提供実験 (https://maps.gsi.go.jp/development/vt.html)
  - 国土地理院ベクトルタイル( https://github.com/gsi-cyberjapan/vector-tile-experiment )
  - 地理院地図ベクトルタイル( https://github.com/gsi-cyberjapan/gsimaps-vector-experiment )
- 政府統計の総合窓口(e-Stat) API機能 (https://www.e-stat.go.jp/api/)
- H-RISK for Wind turbine noise (https://gitlab.com/jtagusari/hrisk-wtn)

## インストール方法

### インストーラーを使用する場合（Windows 10）

1. QGIS (https://qgis.org/) をダウンロード・インストールする
2. H-RISKのインストーラー（[/installer/hrisk-setup.exe](/installer/hrisk-setup.exe)）をダウンロードし，実行する。
3. 必要なコンポーネントがすべてインストールされる
4. QGISでプラグインを有効にする。



### 手動インストール

以下のコンポーネントをそれぞれインストールする必要がある。

- QGIS
- Java（NoiseModellingで必要，環境変数`JAVA_FOR_NOISEMODELLING`の設定も必要）
- NoiseModelling（環境変数`NOISEMODELLING_HOME`の設定も必要）
- H-RISK

例えば，次の手順で設定を行う

1. QGIS (https://qgis.org/) をダウンロード・インストールする
2. このリポジトリのファイルをすべてダウンロードし、QGISのプラグインが保存されているパスに保存する
3. Java実行環境をダウンロードし，適当なフォルダに展開する（NoiseModellingのRequirementsを参照）。
4. Java実行環境のフォルダを環境変数 `JAVA_FOR_NOISEMODELLING` に設定する。
5. NoiseModelling（guiなしバージョン）をダウンロードし，適当なフォルダに展開する。
6. NoiseModellingの展開先フォルダを環境変数 `NOISEMODELLING_HOME` に設定する。



## 開発メモ

### ベクトルタイル利用のためのメモ

#### ズームレベルと緯度経度

ズームレベル0が基準になる。
この地図では，256x256の画像と世界地図（ただし南緯85度~北緯85度程度）が対応する。
経度方向は単純で，1ピクセルが360/256度。ピクセル座標$x$から経度$\mathrm{lng}$は以下の式で計算される
$$
\mathrm{lng}=360\times\dfrac{x-128}{256}
$$
緯度方向は，経度方向ほど簡単ではない。1ピクセルの表す緯度が，赤道付近ほど大きく，極付近ほど小さい。ピクセル座標$y$から経度$\mathrm{lat}$は以下の式で計算される
$$
\sin\left(\dfrac{\pi\cdot\mathrm{lat}}{180}\right)=\tanh\left[-\dfrac{2\pi y}{256}+\tanh^{-1}\left\{\sin\left(\dfrac{\pi}{180}L\right)\right\}\right]
$$
ただし$L=85.05112878$である。

ズームレベル$z$のもとでは，次の式になる。
$$
\mathrm{lng}=360\times\dfrac{x-128}{256\cdot2^z}
$$
$$
\sin\left(\dfrac{\pi\cdot\mathrm{lat}}{180}\right)=\tanh\left[-\dfrac{2\pi y}{256\cdot2^z}+\tanh^{-1}\left\{\sin\left(\dfrac{\pi}{180}L\right)\right\}\right]
$$

日本国内だと，ズームレベル15で256x256タイルは約1km x 1km。

#### 道路中心線

- 国土地理院地図の道路中心線情報を使う( https://github.com/gsi-cyberjapan/experimental_rdcl )
- https://cyberjapandata.gsi.go.jp/xyz/experimental_rdcl/{z}/{x}/{y}.geojson からgeojson形式のファイルが入手可能。ただしズームレベルzは16固定
- およそ500m四方のデータ。

#### 建物

- 地理院地図を使う( https://cyberjapandata.gsi.go.jp/xyz/experimental_bvmap/{z}/{x}/{y}.pbf )
- `Ftcode`で地物の絞り込みができる。ズームレベル14~16で`3101`/ `3102` / `3103` / `3111` / `3112`を取得すればよい。

#### 標高

- 国土地理院地図のDEM-10Bを使う( https://github.com/gsi-cyberjapan/experimental_dem )
- https://cyberjapandata.gsi.go.jp/xyz/experimental_dem10b/{z}/{x}/{y}.geojson からgeojson形式のファイルが入手可能。ただしズームレベルzは18固定

### NoiseModelling導入のためのメモ

#### GUI導入方法

- 上記サイトのRequirements / Get startedにしたがってインストールする。
- Java実行環境が必要だが，インストーラーを使えば，自動で入る。
- Get startedの通り実行する
  - `GeoServer`が立ち上がる。各種設定は`NoiseModelling`にお任せ。色々とwarningが出ているが，将来解決されるのだろう。
  - `WPS`(Web Processing Service)も立ち上がる（`GeoServer`の機能？）。これにアクセスするために`localhost:9580`にアクセス。
  - `GeoServer`には，ジオメトリが`table`として保存されている。
  - `Import_File`プロセス（`noisemodelling/wps/Import_and_Export/Import_File.groovy`スクリプト）によって，shapefile等のファイルを`table`としてインポートできる。デフォルトでは，拡張子は削除され，ファイル名を大文字にしたものが`table`名となる（`buildings.shp -> BUILDINGS`）。

#### CUI導入方法

- `NoiseModelling_._without_gui`が必要
- Javaのインストール／パス設定（Windowsなら`JAVA_HOME`）が必要
  - OpenJDKからzipをダウンロード( https://jdk.java.net/archive/ )。バージョン11のみ動作保証。
  - ファイルを適当なところに展開（たとえば`C:\Program Files\java\jdk-11.0.2`）
  - システム環境変数`JAVA_HOME`を上記パスに設定，コマンドプロンプトから`echo %JAVA_HOME%`で設定できていることを確認
  - `JAVA_HOME`は，`bin/wps_script.bat`で参照されている。
- `bin/wps_scripts`を使って，groovyスクリプトを実行する。
  - windowsでは，普通，拡張子のないファイルは実行できない（`PATH_EXT`参照）。同フォルダにある`wps_scripts.bat`が実行される。
  - コマンドラインでは，`wps_script`の後に，`java`のオプションが並ぶ。
  - `-w ./`: 作業ディレクトリはカレントディレクトリ
  - `-s xxx.groovy`: groovyスクリプト`xxx.groovy`を実行する
- `lib`フォルダには，Java環境で必要なファイルが保存されている。
- `noisemodelling`フォルダ（特に`noisemodelling/wps`）には，groovyスクリプトが保存されている。各々のスクリプトの詳細は，スクリプトの中身をみれば分かる。（引数，返り値，など）
- `resources`フォルダには，サンプルデータが入っている。
- NoiseModellingを動かすとき，普通は，複数のgroovyスクリプトを動かして結果を得る。`get_started_tutorial.groovy`は，その良い例になっている。


```
path/to/wps_script/wps_scripts -2 ./ -s path/to/groovy/test.groovy
```


### インストーラー作成メモ

#### 準備

- `bin/wps_scripts`を作り替えて，`JAVA_HOME`ではなく`JAVA_FOR_NOISEMODELLING`を使うようにしておく。`JAVA_HOME`は，名前が衝突したとき面倒。
- `bin/wps_scripts`を作り替えて，NoiseModellingの各種Javaモジュールを呼び出すために`NOISEMODELLING_HOME`環境変数を使うようにしておく。

#### Java

- OpenJDKのウェブサイト( https://jdk.java.net/archive/ )からJAVA実行環境バージョン11.0.2をダウンロードする
- `C:\Program Files\java`フォルダを作成し，上記でダウンロードしたzipファイルを展開する（`C:\Program Files\java\jdk-11.0.2`となる）
- システム環境変数`JAVA_FOR_NOISEMODELLING`として`C:\Program Files\java\jdk-11.0.2`を設定する

#### NoiseModelling

- NoiseModellingのGitHubページ( https://github.com/Universite-Gustave-Eiffel/NoiseModelling/releases )から`NoiseModelling_without_gui.zip`をダウンロード
- `C:\Program Files\NoiseModelling`フォルダに展開する
- システム環境変数`NOISEMODELLING_HOME`として`C:\Program Files\NoiseModelling`を設定する


#### QGISプラグイン

- QGIS pluginのデフォルトインストールパス(`AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`)に直接展開してしまう。
- 本当は，QGISレポジトリに登録した方がベター。


#### inno setup

上記のプロセスを，inno setupを使ってプログラミング(`installer`フォルダ)


### QGISプラグイン作成メモ

#### 参考ウェブサイト

VS CodeでQGISプラグインが作成できるように準備する

- A tutorial for QGIS Plugin Development in VS Code (https://gispofinland.medium.com/cooking-with-gispo-qgis-plugin-development-in-vs-code-19f95efb1977)
- Getting started with QGIS plugin development in 2022 (https://gispofinland.medium.com/getting-started-with-qgis-plugin-development-in-2022-bbe410dc1332)
- QGIS3 Plugin Builderでプラグイン作成 https://chiakikun.hatenadiary.com/entry/2018/08/16/124941
- QGIS documentation https://www.qgis.org/en/docs/index.html
- RemoteDebuggingQgisVsCode (https://gist.github.com/maximlt/9178dca844ff70c73367d9111197faa8)


#### VS Code環境

下記を実行
```
<QGIS-INSTALLATION-FOLDER>\bin\python-qgis-ltr.bat -m venv .venv
.venv\Scripts\activate
```

環境変数を追加

```
<QGIS-INSTALLATION-FOLDER\>\bin
<QGIS-INSTALLATION-FOLDER\>\apps\qgis-ltr\bin
<QGIS-INSTALLATION-FOLDER\>\apps\Qt5\bin
```

`ptvsd`を使ったデバッグ環境の準備。
QGIS上で`Enable debug for Visual Studio`を走らせておいて，Pythonで以下のスクリプト(`launch.json`)を走らせる。

```
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Remote Attach",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "${workspaceFolder}"
        }
      ],
      "justMyCode": true
    }
  ]
}
```

また，プラグインの`processingAlgorithm`内に，以下のスクリプトが必要。

```
import ptvsd
ptvsd.debug_this_thread()
```



#### 多言語（日本語化）対応

##### ロケール設定

プラグインクラスで，次の様にロケールや使用ファイルを指定しておく。

```{python}
# Initialize the plugin path directory
self.plugin_dir = os.path.dirname(__file__)

# initialize locale
try:
    locale = QSettings().value("locale/userLocale", "en", type=str)[0:2]
except Exception:
    locale = "en"
locale_path = os.path.join(
    self.plugin_dir,
    'i18n',
    'hrisk_{}.qm'.format(locale))
if os.path.exists(locale_path):
    self.translator = QTranslator()
    self.translator.load(locale_path)
    QCoreApplication.installTranslator(self.translator)
```

##### 翻訳関数の設定

アルゴリズムクラスでは，関数`self.tr`を定義しておく。

```
def tr(self, string):
  return QCoreApplication.translate(self.__class__.__name__, string)
```

これを使うときには，単に`self.tr("hogehoge")`とすればよい。
ただし，変数を後で翻訳する場合には，`from qgis.PyQt.QtCore import QT_TRANSLATE_NOOP`とした上で，`QT_TRANSLATE_NOOP("python_script_name","hogehoge")`とする。


##### プロジェクトファイルの作成

翻訳するファイルとそれに利用する`.ts`ファイルを指定する。たとえば，以下のファイル`hrisk.pro`を作成する。

```
SOURCES = estimatelevelofbuilding.py \
estimatepopulationofbuilding.py
TRANSLATIONS = i18n/hrisk_ja.ts
```

##### `.ts`ファイルの作成

翻訳に利用する`.ts`ファイルを作成する。
たとえば，`i18n/hrisk_ja.ts`を作成する。
作成時，ファイルの中身は空で良い。

`.ts`ファイルは，以下のスクリプトで更新する。
なお，既に入力された内容も消去されない模様。

```
python -m PyQt5.pylupdate_main *.pro
```

##### `.qm`ファイルの作成

次のスクリプトで，`.ts`ファイルから`.qm`ファイルが作成される。
```
lrelease *.ts
```