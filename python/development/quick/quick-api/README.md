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
├── README.md                     # プロジェクトの説明
├── app/
│   ├── __init__.py
│   ├── api/                      # API関連
│   │   ├── __init__.py
│   │   └── client.py             # APIクライアント
│   ├── core/                     # コア機能
│   │   ├── __init__.py     
│   │   ├── config.py             # 設定読み込み
│   │   └── logger.py             # ログ設定
│   └── services/                 # サービス層
│       ├── __init__.py
│       └── data_collector.py     # データ収集サービス
├── input/                        # 入力ファイル
│   ├── config/                   # 設定ファイル
│   │   ├── connection_config.yml # API接続設定
│   │   └── logging_config.yml    # ログ設定
│   ├── daily/                    # 日次実行定義
│   │   └── requests.yml          # 日次リクエスト定義
│   └── spot/                     # スポット実行定義
│       └── YYYYMMDD/             # 実行日ごとのディレクトリ
│           └── requests.yml      # スポットリクエスト定義
├── output/                       # 出力ファイル
│   │   └── YYYYMMDD/             # 実行日ごとのディレクトリ
│   ├── daily/                    # 日次実行の出力
│   │       ├── data/             # 取得データ
│   │       └── reports/          # 実行レポート
│   ├── spot/                     # スポット実行の出力
│   │   └── YYYYMMDD/             # 実行日ごとのディレクトリ
│   │       ├── data/             # 取得データ
│   │       └── reports/          # 実行レポート
│   └── logs/                     # ログファイル
│       ├── quick_api.log         # アプリケーションログ
│       └── quick_api_error.log   # エラーログ
├── tests/                         # テストコード
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_client.py
│   ├── test_config.py
│   └── test_data_collector.py
├── main.py                       # メインスクリプト
└── requirements.txt              # 依存関係

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
C:\<rootpath>
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

### リクエスト定義ファイルの作成・管理手順

#### 1. リクエストファイルの基本
##### 1.1 ファイルの種類と配置場所
- 日次実行用: `input/daily/requests.yml`
- スポット実行用: `input/spot/YYYYMMDD/requests.yml`

##### 1.2 基本構造
```yaml
metadata:              # スポット実行時のみ必要
  description: "実行内容の説明"
  created_by: "作成者名"
  created_at: "作成日"

requests:
  エンドポイント名:
    enabled: true      # 実行有無のフラグ
    description: "処理の説明"
    # 以下、必要なパラメータを設定
```
#### 2. 各エンドポイントの設定方法

##### 2.1 経済統計データ（file）
```yaml
# 日次実行用（直近データ取得）
file:
  enabled: true
  description: "経済統計データ（直近）"
  # 日付指定なし -> 直近データを取得

# スポット実行用（特定日）
file:
  description: "経済統計データ"
  date: "20240410"  # 20240410以降の日付のみ指定可能

# スポット実行用（期間指定）
file:
  description: "経済統計データ（期間指定）"
  date_range:
    start_date: "20240410"
    end_date: "20240415"
```
##### 2.2 海外株データ（quote_foreign_stock）
```yaml
quote_foreign_stock:
  description: "海外株データ取得"
  markets:
    - usa_stock   # 北米株
    - lse_stock   # LSE（英国）株
    - hk_stock    # 香港株
```

##### 2.3 その他のエンドポイント
```yaml
# 各種指標データ
quote_index:
  enabled: true
  description: "各種指標・直近データ"

# 国内株データ
quote_stock:
  enabled: true
  description: "国内株・直近データ"

# 国内投信データ
fund:
  enabled: true
  description: "国内投信・基本データ"

# 外国投信データ
foreign_fund:
  enabled: true
  description: "外国投信・直近データ"
```


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

#### 3. メンテナンス手順

##### 3.1 日次実行定義のメンテナンス
1. 定期的な見直し項目
   - enabled フラグの確認
   - 不要なエンドポイントの削除
   - 新規追加が必要なエンドポイントの追加
     → connection_config.yml の 定義を先に確認

2. チェックポイント
   - fileエンドポイントには日付指定がないことを確認
   - markets指定の内容が最新であることを確認
   - description の内容が実態と合っているか確認

##### 3.2 スポット実行定義の管理
1. ファイル配置
   - 日付ディレクトリの作成: `input/spot/YYYYMMDD/`
   - requests.yml の配置
   - 実行後の整理（必要に応じてアーカイブ）

2. 作成時の注意点
   - metadata セクションの必須入力
   - file エンドポイントの日付指定（20240410以降）
   - markets 指定時の市場コード確認

#### 4. その他


1. 命名規則
   - ファイル名は小文字のみ使用
   - 日付は必ずYYYYMMDD形式
   - description は具体的な内容を記載

2. コメント
   - 各セクションの目的を記載
   - 特殊な設定がある場合は理由を記載
   - 一時的な変更は期間を明記

3. 実行エラー時は？
   - レート制限エラー
     → 時間をおいて再実行
   - データ取得エラー
     → ログを確認し、必要に応じて再実行
   - 契約状況
     → file エンドポイントは現在利用不可？  

## 使用方法

### 日次実行

```bash
python main.py --mode daily
```

### スポット実行

```bash
python main.py --mode spot --date 20231208
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
pytest tests/test_client.py

# 特定のテストクラスを実行
pytest tests/test_client.py::TestQuickApiClient

# 特定のテストメソッドを実行
pytest tests/test_client.py::TestQuickApiClient::test_init_client
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
