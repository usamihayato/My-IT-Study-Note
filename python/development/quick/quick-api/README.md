# Quick Api

## 概要

## 機能


## 必要要件
- Python 3.10以上
- 必要なパッケージは`requirements.txt`に記載

## 使い方

1. 設定ファイルの準備

     1-1.

2. 実行コマンド

日次実行の場合：
>python src/app/main.py --mode daily

スポット実行の場合：
>python src/app/main.py --mode spot --date 20231208



## ディレクトリ構成
```
project_root/
├── README.md                    # プロジェクトの説明
├── pyproject.toml               # Poetry依存関係管理
├── .gitignore
│
├── src/                         # ソースコード
│   └── app/
│       ├── __init__.py
│       ├── main.py              # メインスクリプト
│       │
│       ├── core/                # コア機能
│       │   ├── __init__.py
│       │   ├── config.py        # 設定読み込み
│       │   └── logger.py        # ログ設定
│       │
│       ├── api/                 # API関連
│       │   ├── __init__.py
│       │   └── client.py        # APIクライアント
│       │
│       └── utils/               # ユーティリティ
│           ├── __init__.py
│           └── file_handler.py  # ファイル保存処理
│
├── input/                       # 入力ファイル
│   ├── config/                  # 設定ファイル
│   │   ├── connection_config.yml    # API接続設定
│   │   └── logging_config.yml       # ログ設定
│   │
│   ├── daily/                        # 日次実行の定義
│   │   └── requests.yml
│   └── spot/                         # スポット実行の定義
│       ├── 20231201/                 # 日付ごとのディレクトリ
│       │   └── requests.yml
│       └── 20231208/
│           └── requests.yml
│
├── output/                      # 出力ファイル
│   ├── logs/                    # ログファイル
│   │   └── .gitkeep
│   └── extracted_data/          # API取得データの保存先
│       └── .gitkeep
│
└── tests/                       # テスト
    ├── __init__.py
    ├── conftest.py              # テスト設定
    └── test_api/                # APIテスト
```