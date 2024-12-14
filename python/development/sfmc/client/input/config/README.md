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