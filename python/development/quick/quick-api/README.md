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

### インストール

```bash
# 環境の作成
conda create -n quick-api python=3.10

# 環境の有効化
conda activate quick-api

# 必要なパッケージのインストール
conda install pyyaml requests urllib3
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