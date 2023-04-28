# H-RISK (QGIS plugin)

## About

This pluin implements 
- NoiseModelling (https://github.com/Universite-Gustave-Eiffel/NoiseModelling)
- fetch geometries from GSI vector tile(https://github.com/gsi-cyberjapan/gsimaps-vector-experiment)
- estimation of health risks posed by road traffic noise in Japan

## Structure

- hrisk_provider
- algabstract (abstract class)
  - fetchabstract (abstract class)
    - fetchja...
  - receiverabstract (abstract class)
    - receiver...
  - noiseabstract (abstract class)
    - noise...
  - source...
  - estimate...
  - isosurface


## Developing memo (in Ja)


### 目論見

- 国内，任意の1kmメッシュ（程度）を対象として自動車騒音マップを作成する
- QGIS上で動く
- Open Dataを使う
  - 国土地理院ベクトルタイル( https://github.com/gsi-cyberjapan/vector-tile-experiment )
  - 地理院地図ベクトルタイル( https://github.com/gsi-cyberjapan/gsimaps-vector-experiment )

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
- `Ftcode`で地物の絞り込みができる。ズームレベル14~16で`3101`/ `3102` / `3103` / `3111` / `3112`を取得すればよいか。

#### 標高

- 国土地理院地図のDEM-10Bを使う( https://github.com/gsi-cyberjapan/experimental_dem )
- https://cyberjapandata.gsi.go.jp/xyz/experimental_dem10b/{z}/{x}/{y}.geojson からgeojson形式のファイルが入手可能。ただしズームレベルzは18固定

### NoiseModelling導入のためのメモ

- 公式: https://noisemodelling.readthedocs.io/en/latest/#

#### GUI

- 上記サイトのRequirements / Get startedにしたがってインストールする。
- JAVAランタイムが必要だが，インストーラーを使えば，自動で入る。
- Get startedの通り実行する
  - `GeoServer`が立ち上がる。各種設定は`NoiseModelling`にお任せ。色々とwarningが出ているが，将来解決されるのだろう。
  - `WPS`(Web Processing Service)も立ち上がる（`GeoServer`の機能？）。これにアクセスするために`localhost:9580`にアクセス。
  - `GeoServer`には，ジオメトリが`table`として保存されている。（ソフトを再起動しても消えないので，どこかに保存しているのだろう）
  - `Import_File`プロセス（`noisemodelling/wps/Import_and_Export/Import_File.groovy`スクリプト）によって，shapefile等のファイルを`table`としてインポートできる。デフォルトでは，拡張子は削除され，ファイル名を大文字にしたものが`table`名となる（`buildings.shp -> BUILDINGS`）。

#### without GUI (CUI)

- `NoiseModelling_._without_gui`が必要
- Javaのインストール／パス設定（Windowsなら`JAVA_HOME`）が必要
  - OpenJDKからzipをダウンロード( https://jdk.java.net/archive/ )。バージョン11のみ動作保証。
  - ファイルを適当なところに展開（たとえば`C:\Program Files\java\jdk-11.0.2`）
  - システム環境変数`JAVA_HOME`を上記パスに設定，コマンドプロンプトから`echo %JAVA_HOME%`で設定できていることを確認
- `bin`フォルダの`wps_scripts`を使って，groovyスクリプトが実行可能な環境を呼び出す。
  - windowsでは，普通，拡張子のないファイルは実行できない（`PATH_EXT`参照）。同フォルダにある`wps_scripts.bat`が実行される。
  - コマンドラインでは，`wps_script`の後に，`java`のオプションが並ぶ。
  - `-w ./`: 作業ディレクトリはカレントディレクトリ
  - `-s xxx.groovy`: groovyスクリプト`xxx.groovy`を実行する
- `lib`フォルダには，Java環境で必要なファイルが保存されている。
- `noisemodelling`フォルダ（特に`noisemodelling/wps`）には，groovyスクリプトが保存されている。各々のスクリプトの詳細は，スクリプトの中身をみれば分かる。（引数，返り値，など）
- `resources`フォルダには，サンプルデータが入っている。
- NoiseModellingを動かすとき，普通は，複数のgroovyスクリプトを動かして結果を得る。`get_started_tutorial.groovy`は，その良い例になっている。

結局，groovyスクリプトを動かせればNoiseModellingを動かせるのだが，そのためにはJAVA環境が必要。
JAVA環境のセットアップをしているのが`wps_scripts`なので，常にここから動かす様にすればよい。
pythonでは，`subprocess`から`wps_scripts`を動かせばよいはず。

```
path/to/wps_script/wps_scripts -2 ./ -s path/to/groovy/test.groovy
```


### インストーラー作成のためのメモ


- JAVAのインストール
  - OpenJDKのウェブサイト( https://jdk.java.net/archive/ )からJAVA実行環境バージョン11.0.2をダウンロードする
  - `C:\Program Files\java`フォルダを作成し，上記でダウンロードしたzipファイルを展開する（`C:\Program Files\java\jdk-11.0.2`となる）
  - システム環境変数`JAVA_HOME`として`C:\Program Files\java\jdk-11.0.2`を設定する
- NoiseModellingのインストール
  - NoiseModellingのGitHubページ( https://github.com/Universite-Gustave-Eiffel/NoiseModelling/releases )から`NoiseModelling_without_gui.zip`をダウンロード
  - ファイルを展開
  - システム環境変数`NoiseModelling`を解凍したフォルダに設定する
- QGIS pluginのインストール
  - ( https://qgis.org/ja/site/forusers/download.html )


PowerShellで自動化したい。。
( https://rainbow-engine.com/software-install-from-batch/ )

### python環境準備のメモ

QGISプラグイン作成にも関係するが。

https://gispofinland.medium.com/cooking-with-gispo-qgis-plugin-development-in-vs-code-19f95efb1977

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

https://gispofinland.medium.com/getting-started-with-qgis-plugin-development-in-2022-bbe410dc1332

### QGISプラグインの作成メモ

#### 参考サイト

- QGIS3 Plugin Builderでプラグイン作成 https://chiakikun.hatenadiary.com/entry/2018/08/16/124941
- QGIS documentation https://www.qgis.org/en/docs/index.html



#### デバッグ環境
https://gist.github.com/maximlt/9178dca844ff70c73367d9111197faa8 参照。

- `ptvsd`を使う。
- QGIS上で`Enable debug for Visual Studio`を走らせておいて，Pythonで以下のスクリプト(`launch.json`)を走らせる。

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

また，`processingAlgorithm`内に，以下のスクリプトが必要。

```
import ptvsd
ptvsd.debug_this_thread()
```



### 日本語化のためのメモ

コード内に日本語を混入させたくないので，英語で作成してから日本語化する。

#### pythonクラスでのロケールの記述

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

#### 翻訳関数の指定

次の様に関数`self.tr`を定義しておく。

```
def tr(self, string):
  return QCoreApplication.translate(self.__class__.__name__, string)
```

これを使うときには，単に`self.tr("hogehoge")`とすればよい。
ただし，変数を後で翻訳する場合には，`from qgis.PyQt.QtCore import QT_TRANSLATE_NOOP`とした上で，`QT_TRANSLATE_NOOP("python_script_name","hogehoge")`とする。

#### `.pro`ファイルの作成

翻訳するファイルとそれに利用する`.ts`ファイルを指定する。たとえば，以下のファイル`hrisk.pro`を作成する。

```
SOURCES = estimatelevelofbuilding.py \
estimatepopulationofbuilding.py
TRANSLATIONS = i18n/hrisk_ja.ts
```

#### `.ts`ファイルの作成

翻訳に利用する`.ts`ファイルを作成する。
たとえば，`i18n/hrisk_ja.ts`を作成する。
作成時，ファイルの中身は空で良い。

`.ts`ファイルは，以下のスクリプトで更新する。
なお，既に入力された内容も消去されない模様。
```
python -m PyQt5.pylupdate_main *.pro
```

#### `.qm`ファイルの作成

次のスクリプトで，`.ts`ファイルから`.qm`ファイルが作成される。
```
lrelease *.ts
```


