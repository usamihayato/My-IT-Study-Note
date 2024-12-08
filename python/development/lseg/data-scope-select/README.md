# LSEG DataScope Select API
LSEG社の DSS(DataScope Select) APIからデータを取得し、ファイルとして保存するツール

## 概要
- DSS APIを使用してデータを取得
- 取得したデータをCSVファイルとして保存
- 複数銘柄の一括取得に対応
- ログ機能とエラーハンドリングを実装

## 機能
- 株価データの自動取得
- 設定ファイルによる柔軟な設定
- エラー発生時の再試行機能
- 構造化ログによる実行状況の記録

## 必要要件
- Python 3.9以上
- 必要なパッケージは`pyproject.toml`に記載

## 使い方
1. 環境変数の設定
2. 設定ファイルの準備
3. 実行コマンド


## ディレクトリ構成
```
project_root/
├── README.md                    # プロジェクトの説明
├── pyproject.toml               # Poetry依存関係管理
├── .env.example                 # 環境変数テンプレート
├── .gitignore
│
├── src/                         # ソースコード
│   └── app/
│       ├── __init__.py
│       ├── main.py             # メインスクリプト
│       │
│       ├── core/               # コア機能
│       │   ├── __init__.py
│       │   ├── config.py       # 設定読み込み
│       │   └── logger.py       # ログ設定
│       │
│       ├── api/                # API関連
│       │   ├── __init__.py
│       │   └── client.py       # APIクライアント
│       │
│       └── utils/              # ユーティリティ
│           ├── __init__.py
│           └── file_handler.py # ファイル保存処理
│
├── config/                     # 設定ファイル
│   ├── connection_config.yml   # API接続設定
│   ├── data_config.yml        # データ保存設定
│   └── logging_config.yml     # ログ設定
│
├── data/                      # データファイル
│   ├── symbols.csv            # 銘柄マスタ
│   └── output/                # API取得データの保存先
│       └── .gitkeep
│
├── logs/                      # ログファイル
│   └── .gitkeep
│
└── tests/                     # テスト
    ├── __init__.py
    ├── conftest.py            # テスト設定
    └── test_api/              # APIテスト
```