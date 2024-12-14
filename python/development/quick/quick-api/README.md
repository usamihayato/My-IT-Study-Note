# Quick API Client

Quick APIからデータを取得するためのクライアントツール。

## 機能
- 各種指標データの取得
- 日次実行とスポット実行の対応
- データ取得結果のCSV保存
- 実行結果レポートの生成
- ログ出力

## ディレクトリ構成
```
project_root/
├── README.md                    # プロジェクトの説明
├── src/                         # ソースコード
│   └── app/
│       ├── __init__.py
│       ├── main.py              # メインスクリプト
│       ├── api/                 # API関連
│       │   ├── __init__.py
│       │   └── client.py        # APIクライアント
│       ├── core/                # コア機能
│       │   ├── __init__.py
│       │   ├── config.py        # 設定読み込み
│       │   └── logger.py        # ログ設定
│       └── services/            # サービス層
│           ├── __init__.py
│           └── data_collector.py # データ収集サービス
│
├── input/                       # 入力ファイル
│   ├── config/                  # 設定ファイル
│   │   ├── connection_config.yml    # API接続設定
│   │   └── logging_config.yml       # ログ設定
│   ├── daily/                  # 日次実行定義
│   │   └── requests.yml       # 日次リクエスト定義
│   └── spot/                   # スポット実行定義
│       └── YYYYMMDD/          # 実行日ごとのディレクトリ
│           └── requests.yml   # スポットリクエスト定義
│
└── output/                      # 出力ファイル
    ├── daily/                   # 日次実行の出力
    │   └── YYYYMMDD/           # 実行日ごとのディレクトリ
    │       ├── data/           # 取得データ
    │       └── reports/        # 実行レポート
    ├── spot/                    # スポット実行の出力
    │   └── YYYYMMDD/           # 実行日ごとのディレクトリ
    │       ├── data/           # 取得データ
    │       └── reports/        # 実行レポート
    └── logs/                    # ログファイル
        ├── quick_api.log        # アプリケーションログ
        └── quick_api_error.log  # エラーログ

```


## 環境設定

### 必要条件

- Python 3.10以上
- 必要なパッケージ:
  - pyyaml
  - requests
  - urllib3
  - pytest (テスト実行用)
  - pytest-cov (カバレッジレポート用)

### インストール

```bash
# 環境の作成
conda create -n quick-api python=3.10

# 環境の有効化
conda activate quick-api

# 必要なパッケージのインストール
conda install pyyaml requests urllib3
pip install pytest pytest-cov
```
#### PYTHONPATH の設定

##### conda環境での設定（推奨）

conda環境で恒久的にPYTHONPATHを設定する場合：

1. conda環境のsite-packagesディレクトリにpth文件を作成

```bash
# conda環境のsite-packagesディレクトリを確認
python -c "import site; print(site.getsitepackages()[0])"
```

2. 表示されたパスに `quick-api.pth` ファイルを作成
例：`<表示されたパス>\Lib\site-packages\quick-api.pth`

3. pthファイルに以下の内容を記載（プロジェクトの絶対パスを指定）
```
C:\<rootpath>\src
```

## 設定

### API接続設定（connection_config.yml）

```yaml
api:
  base_url: "https://staging.api.quick-co.jp/octpath/v1/api"
  access_key: "your_access_key"
  timeout: 30
  format: "csv"  # レスポンス形式（csv, json, tsv）
```

### リクエスト定義

#### 日次実行（input/daily/requests.yml）
以下のフォーマットで日次で取得するデータを定義します：

```yaml
# 日次データ取得定義
requests:
  # インターフェース名はconnection_config.ymlのendpoints定義に合わせる
  quote_index:
    enabled: true    # 実行有無のフラグ
    description: "各種指標の日次データ取得"  # 処理の説明

  # universe_next（ページング）対応の場合の例(同じ)
  domestic_stock:
    enabled: true
    description: "国内株の日次データ取得"

  # 市場指定が必要な場合の例
  foreign_stock:
    enabled: true
    description: "海外株の日次データ取得"
    markets:        # 取得対象の市場を指定
      - usa_stock   # 北米株
      - hk_stock    # 香港株
      - lse_stock   # ロンドン株
```

## 使用方法

### 日次実行

```bash
python src/app/main.py --mode daily
```

### スポット実行

```bash
python src/app/main.py --mode spot --date 20231208
```

## 出力ファイル

### データファイル

- 形式: `{endpoint}_{YYYYMMDD_HHMMSS}.csv`
- 保存場所:
  - 日次実行: `output/daily/YYYYMMDD/data/`
  - スポット実行: `output/spot/YYYYMMDD/data/`

### 実行レポート

- 形式: `execution_report_{YYYYMMDD_HHMMSS}.txt`
- 保存場所:
  - 日次実行: `output/daily/YYYYMMDD/reports/`
  - スポット実行: `output/spot/YYYYMMDD/reports/`

### ログファイル

- アプリケーションログ: `output/logs/quick_api.log`
- エラーログ: `output/logs/quick_api_error.log`

## テスト実行
### ユニットテスト

```bash
# プロジェクトルートで実行
pytest

# 詳細な出力を表示
pytest -v

# 特定のテストファイルを実行
pytest tests/test_api/test_client.py

# 特定のテストクラスを実行
pytest tests/test_api/test_client.py::TestQuickApiClient

# 特定のテストメソッドを実行
pytest tests/test_api/test_client.py::TestQuickApiClient::test_init_client
```

### カバレッジレポート作成

```bash

# カバレッジレポートを生成
pytest --cov=app tests/

# HTMLレポートを生成
pytest --cov=app --cov-report=html tests/
# report/htmlディレクトリにレポートが生成されます

```


### テストディレクトリ構成

- `tests/`: テストコードのルートディレクトリ
  - `conftest.py`: pytest共通設定、フィクスチャ定義
  - `test_api/`: APIクライアント関連のテスト
  - `test_core/`: コア機能のテスト
  - `test_services/`: サービス層のテスト

### テスト実行時の注意点

- テストデータは `output/test` ディレクトリに出力されます
- テスト実行後、テストで生成されたデータは自動的にクリーンアップされます
- 本番の設定ファイルやデータには影響を与えません

## 出力ファイル

### データファイル

- 形式: `{endpoint}_{YYYYMMDD_HHMMSS}.csv`
- 保存場所:
  - 日次実行: `output/daily/YYYYMMDD/data/`
  - スポット実行: `output/spot/YYYYMMDD/data/`
  - テスト実行: `output/test/YYYYMMDD/data/`

### 実行レポート

- 形式: `execution_report_{YYYYMMDD_HHMMSS}.txt`
- 保存場所:
  - 日次実行: `output/daily/YYYYMMDD/reports/`
  - スポット実行: `output/spot/YYYYMMDD/reports/`
  - テスト実行: `output/test/YYYYMMDD/reports/`

### ログファイル

- アプリケーションログ: `output/logs/quick_api.log`
- エラーログ: `output/logs/quick_api_error.log`
