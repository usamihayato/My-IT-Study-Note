# SFMC API Integration Project Structure

## Directory Structure
```
sfmc-api-integration/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── service.py        # 認証関連のビジネスロジック
│   │   │   └── models.py         # 認証関連のデータモデル
│   │   ├── data_extension/
│   │   │   ├── __init__.py
│   │   │   ├── service.py        # DE操作のビジネスロジック
│   │   │   ├── models.py         # DEのデータモデル
│   │   │   └── schemas.py        # CSVバリデーションスキーマ
│   │   ├── email/
│   │   │   ├── __init__.py
│   │   │   ├── service.py        # メール送信のビジネスロジック
│   │   │   └── models.py         # メール関連のデータモデル
│   │   └── client.py             # 共通APIクライアント
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # 設定管理
│   │   └── logger.py             # ロギング設定
│   └── utils/
│       ├── __init__.py
│       ├── csv_handler.py        # CSV処理ユーティリティ
│       └── validators.py         # 共通バリデーション
├── input/
│   ├── config/
│   │   ├── connection_config.yml  # 接続設定
│   │   ├── logging_config.yml     # ログ設定
│   │   └── request_config.yml     # リクエスト設定
│   ├── daily/                     # 日次実行用入力ディレクトリ
│   └── spot/                      # スポット実行用入力ディレクトリ
├── output/
│   ├── daily/                     # 日次実行の出力
│   └── spot/                      # スポット実行の出力
├── tests/                         # テストコード
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_data_extension.py
│   └── test_email.py
├── main.py                        # アプリケーションのエントリーポイント
└── requirements.txt               # 依存関係

```

## Implementation Details

### 1. 認証処理 (app/api/auth)
- `service.py`:
  - トークン取得・管理
  - トークンの有効期限管理
  - リトライロジック
- `models.py`:
  - AuthToken データクラス
  - TokenExpiredError 等の例外クラス

### 2. データエクステンション処理 (app/api/data_extension)
- `service.py`:
  - DEへのデータUpsert
  - CSVファイル読み込み
  - バッチ処理ロジック
- `models.py`:
  - DERow データクラス
  - DEConfiguration データクラス
- `schemas.py`:
  - CSVカラムバリデーション
  - データ型変換ルール

### 3. メール送信処理 (app/api/email)
- `service.py`:
  - トリガーメール送信
  - バッチ送信管理
  - 送信状態管理
- `models.py`:
  - EmailTrigger データクラス
  - RecipientData データクラス

### 4. 共通機能
- CSV処理 (`utils/csv_handler.py`):
  - CSVファイル読み込み
  - データ型変換
  - エラーハンドリング
- バリデーション (`utils/validators.py`):
  - 共通入力検証
  - データフォーマットチェック
- ロギング (`core/logger.py`):
  - 構造化ログ
  - ログローテーション
  - エラー通知

## 実装優先順位

1. 基盤整備(done)
   - ディレクトリ構造の作成
   - 共通クライアントの実装
   - 設定ファイルの整備
   - ロギング設定

2. 認証処理
   - トークン管理機能
   - エラーハンドリング
   - リトライロジック

3. データエクステンション処理
   - CSVファイル読み込み機能
   - バリデーション実装
   - Upsert処理実装
   - エラーハンドリング

4. メール送信処理
   - トリガー送信機能
   - 送信状態管理
   - エラーハンドリング

5. テスト実装
   - ユニットテスト
   - 統合テスト
   - モックサーバーテスト

## 注意点
- エラーハンドリングの徹底
- ロギングの充実
- バッチ処理の最適化
- リトライ処理の実装
- テストカバレッジの確保