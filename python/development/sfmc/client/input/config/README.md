# Config
## connection_config.yml
### 公式ベストプラクティスに基づく設定

#### apiエンドポイント
```yaml
sfmc:
  base_url: "https://your-subdomain.rest.marketingcloudapis.com"
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  account_id: "your_mid"  # MID（Business Unit ID）

```

- base_url: インスタンス固有のエンドポイント
    - 形式: https://{subdomain}.rest.marketingcloudapis.com
    - 認証時に返されるrest_instance_urlを使用する必要がある

- account_id（MID）: Business UnitのMIDを指定
    - Parent Business UnitのMIDを使用することで、すべてのChild Business Unitにアクセス可能
    - APIドキュメントでは特定の操作でMIDが必要とされています

#### 接続基本設定:

```yaml
connection:
  keep_alive: true
  keep_alive_timeout: 4  # サーバー側は5秒
```
- HTTP永続接続:

    - 公式推奨: 5秒未満のkeep-alive timeout
    - 設定値: 4秒（サーバー側の5秒より短く設定）
        - 理由: サーバー側のタイムアウトによる接続エラーを防止

#### レート制限
```yaml
rate_limits:
  transactional_messaging:
    per_minute: 2400
    max_batch_size: 50
  rest_api:
    per_minute: 36
    per_hour: 360
    per_day: 410
```

値は公式のベストプラクティスより
- トランザクショナルメッセージング: 1分あたり2400リクエスト
- 通常のREST API: 1分あたり36リクエスト

#### リトライ設定
```yaml
retry:
  max_attempts: 2
  initial_wait_seconds: 2.0
  backoff_factor: 2
  status_forcelist:
    - 408  # Request Timeout
    - 429  # Too Many Requests
    - 500  # Internal Server Error
    # ... その他のサーバーエラー
```

- 指数バックオフによるリトライ
- サーバーエラー時のみリトライ
- クライアントエラー（400番台）はリトライ対象外

#### メッセージング設定
```yaml
messaging:
  message_key_ttl_hours: 72  # 公式要件
  batch_processing:
    chunk_size: 50
    delay_between_chunks: 1
```
- メッセージキーの一意性: 72時間（公式要件）
- バッチサイズ: 50件（公式推奨値）

### カスタム設定

#### 接続プール設定
```yaml
connection:
  pool_connections: 10
  pool_maxsize: 10
```
通常の運用では不要

設定が必要となるケース：
- 大規模なバッチ処理を頻繁に行う場合
- マイクロサービス環境で複数のサービスが共有する場合
- 高頻度のトランザクショナルメール送信を行う場合

#### プロキシ設定
```yaml
use_proxy: true
proxies:
  host: "proxy.example.com"
  port: 8080

```

### 設定値の調整方法
#### 環境別の推奨設定

##### 開発環境
```yaml
retry:
  max_attempts: 2
  initial_wait_seconds: 1.0
```

##### 本番環境
```yaml
retry:
  max_attempts: 2
  initial_wait_seconds: 2.0
```

#### タイムアウト設定の調整

- 通常のAPI利用: 30秒
- 大量データ処理時: 60秒まで延長可能

#### トラブルシューティング

1. 接続エラーが発生する場合
    - プロキシ設定の確認
    - タイムアウト値の調整
    - Keep-Alive設定の確認


1. レート制限エラーが発生する場合

    - バッチ処理の分散
    - チャンク間の待機時間の調整
    - 同時実行数の制御


1. 認証エラーが発生する場合

    - クライアントID/シークレットの確認
    - アクセス権限の確認
    - トークンの有効期限の確認

### Transactional Messaging API Best Practices
こちら参照:
https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/transactional-messaging-best-practices.html

## logging_config.yml

### 出力先

1. コンソール出力

    - レベル: INFO以上
    - 用途: 開発時のデバッグ、実行状況の確認


1. 通常ログファイル

    - ファイル: output/logs/sfmc_api.log
    - レベル: DEBUG以上
    - 用途: 詳細な実行ログ、トラブルシューティング


1. エラーログファイル

    - ファイル: output/logs/sfmc_api_error.log
    - レベル: ERROR以上
    - 用途: エラー監視、障害分析
## request_config.yml

### 現在の設定内容

#### 基本構造
```yaml
# 入力設定
input:
  base_dir: "input"            # 入力のベースディレクトリ
  daily_dir: "daily"          # 日次実行用ディレクトリ
  spot_dir: "spot"            # スポット実行用ディレクトリ
  request_file: "request.csv" # 処理対象のファイル名

# 出力設定
output:
  base_dir: "output"          # 出力のベースディレクトリ
  daily_dir: "daily"          # 日次実行の出力ディレクトリ
  spot_dir: "spot"            # スポット実行の出力ディレクトリ

# ファイル形式設定
file_format:
  encoding: "utf-8"
  delimiter: ","
  newline: "\n"

# 実行モード設定
execution:
  allowed_modes:              
    - "daily"
    - "spot"
  default_mode: "daily"
```

### ディレクトリ構造
```
sfmc-api-integration/
├── input/
│   ├── daily/
│   │   └── request.csv        # 日次処理用の入力ファイル
│   └── spot/
│       └── YYYYMMDD/          # 処理日付のディレクトリ
│           └── request.csv    # スポット処理用の入力ファイル
│
└── output/
    ├── daily/
    │   └── YYYYMMDD/         # 処理日付のディレクトリ
    │       └── data/         # 処理結果
    └── spot/
        └── YYYYMMDD/         # 処理日付のディレクトリ
            └── data/         # 処理結果
```

### 要検討事項

#### 1. 入力ファイル仕様
- [ ] CSVのカラム定義
  ```yaml
  # 例：想定されるカラム定義
  columns:
    - name: "email"
      type: "string"
      required: true
      validation: "email"
    - name: "subscriber_key"
      type: "string"
      required: true
    # 他のカラムも同様に定義
  ```

- [ ] バリデーションルール
  - データ型チェック
  - 必須項目チェック
  - フォーマットチェック（メールアドレスなど）
  - 文字数制限

- [ ] エラーハンドリング
  - バリデーションエラー時の処理
  - エラーレコードの出力方法

#### 2. 出力ファイル仕様
- [ ] ファイル種類と命名規則
  ```yaml
  # 例：出力ファイルの定義
  output_files:
    success:
      name_format: "success_%Y%m%d_%H%M%S.csv"
      retention_days: 30
    error:
      name_format: "error_%Y%m%d_%H%M%S.csv"
      retention_days: 30
  ```

- [ ] 出力データ形式
  - 成功/失敗レコードの区分け
  - エラー内容の記録方法
  - レスポンスデータの保存形式

#### 3. 処理ルール
- [ ] バッチ処理設定
  ```yaml
  # 例：バッチ処理の設定
  batch:
    size: 50                # 1バッチあたりの処理件数
    parallel: false         # 並行処理の有無
    error_threshold: 0.1    # エラー率の閾値（10%）
  ```

- [ ] リカバリー処理
  - 途中失敗時の再開方法
  - 重複チェックの方法
  - 処理済みレコードの管理

#### 4. 運用設定
- [ ] ジョブ実行パラメータ
  ```yaml
  # 例：実行時パラメータ
  job:
    timeout: 3600          # 実行タイムアウト（秒）
    retry:
      max_attempts: 3      # 最大リトライ回数
      interval: 300        # リトライ間隔（秒）
  ```

- [ ] 監視設定
  - 処理の進捗状況
  - パフォーマンスメトリクス
  - アラート条件

### 実装の優先順位

1. 基本機能
   - [x] ディレクトリ構造の定義
   - [x] 基本的な設定ファイル形式
   - [x] 実行モードの管理

2. 入力処理
   - [ ] CSVファイル読み込み
   - [ ] 基本的なバリデーション
   - [ ] エラーハンドリング

3. 出力処理
   - [ ] 処理結果の保存
   - [ ] エラーログの出力
   - [ ] ファイル管理

4. 拡張機能
   - [ ] 並行処理
   - [ ] パフォーマンス最適化
   - [ ] 監視機能

### 今後の検討事項
1. データ型とバリデーションの詳細定義
2. エラー処理の詳細フロー
3. パフォーマンスチューニングの指針
4. 運用監視の要件
