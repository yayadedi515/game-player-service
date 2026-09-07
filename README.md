# Game Player Service

[![CI](https://github.com/yayadedi515/game-player-service/actions/workflows/ci.yml/badge.svg)](https://github.com/yayadedi515/game-player-service/actions/workflows/ci.yml)

**日本語** | [简体中文](#中文说明)

プレイヤー管理を題材に、FastAPI、PostgreSQL、Redis、JWT認証、所有権・ロール認可、pytestによる自動テスト、Docker、Railwayへのデプロイを実践したPythonバックエンドのポートフォリオです。

ユーザー登録・ログイン、プレイヤー管理、管理者によるスコア追加、プレイヤー間のスコア移動、移動履歴、Redisランキングキャッシュなどを実装しています。

## 公開デモ

* API：https://game-player-service-production.up.railway.app/
* Swagger UI：https://game-player-service-production.up.railway.app/docs

> [!IMPORTANT]
> 現在、FastAPI、Service層、PostgreSQL Repository、Redisキャッシュを接続し、JWT認証と所有権・ロール認可を含むAPIをRailway上で公開しています。
> 旧インメモリ版のServiceは、基礎的な業務ロジックとJSON保存を確認する`legacy_player_service.py`として残しています。


## 現在の構成

| レイヤー                  | 主な機能                                   | 主な接続先                       |
| --------------------- | -------------------------------------- | --------------------------- |
| FastAPI API / Router  | HTTPリクエスト・レスポンス、Pydantic入力検証、依存関係の取得   | PlayerService / UserService |
| Service               | プレイヤー・認証ユースケース、業務結果・業務例外、所有権・ロール認可     | Repository Protocol         |
| PostgreSQL Repository | プレイヤー、ユーザー、スコア移動履歴のSQLとトランザクション        | PostgreSQL                  |
| Redis Ranking Cache   | ランキングの読み取りキャッシュ、TTL、更新時の無効化、障害時フォールバック | Redis                       |
| 管理CLI                 | 既存ユーザーの管理者ロールへの昇格                      | UserService                 |
| Legacy PlayerService  | 基礎的な業務ロジック、JSON保存・読込                   | メモリ／JSON                    |

現在の正式なAPI経路は次のとおりです。

* 通常処理：HTTP → FastAPI Router → Service → Repository → Psycopg → PostgreSQL
* ランキング取得：PlayerService → RedisRankingCache。キャッシュミス時だけPlayerRepositoryからPostgreSQLを参照
* 認証処理：Bearer Token → `get_current_user` → JWT検証 → UserRepositoryから最新のユーザーとロールを取得

## 主な実装内容

* プレイヤー名の前後空白を除去
* 空白名および重複名の拒否
* スコア降順、同点時は名前昇順のランキング
* JSON形式での保存と読込
* パラメータ化SQLによるデータベース操作
* PostgreSQLの主キー、外部キー、UNIQUE制約、CHECK制約
* `SELECT ... FOR UPDATE`による行ロック
* 固定された順序でのロック取得
* スコア移動と履歴追加を同一トランザクションで実行
* データベース例外発生時のロールバック
* pytestによるコンポーネントテスト、APIテスト、Repository統合テスト

## 技術スタック

* Python 3.11
* FastAPI
* Pydantic
* pydantic-settings
* Uvicorn
* PostgreSQL
* Psycopg 3
* SQLAlchemy
* Alembic
* python-dotenv
* pytest
* HTTPX2
* Git
* Docker
* GitHub Actions
* Docker Compose
* Redis
* redis-py
* pwdlib
* Argon2
* PyJWT
* pwdlib / Argon2
* Railway

## API

プレイヤー情報はPostgreSQLの`players`テーブルに保存されます。FastAPI起動時にサンプルプレイヤーは自動登録されません。

| Method   | Endpoint                  | 説明                             | 認証         |
|----------|---------------------------|----------------------------------|--------------|
| `GET`    | `/health`                 | ヘルスチェック                   | 不要         |
| `GET`    | `/players/{name}`         | プレイヤーの取得                 | 不要         |
| `GET`    | `/ranking`                | ランキングの取得                 | 不要         |
| `POST`   | `/players`                | プレイヤーの作成                 | Bearer Token |
| `DELETE` | `/players/{name}`         | プレイヤーの削除                 | Bearer Token |
| `PATCH`  | `/players/{name}/score`   | スコアの追加                     | Bearer Token |
| `POST`   | `/transfers`              | スコアの移動                     | Bearer Token |
| `GET`    | `/transfers`              | 移動履歴の取得（ページング対応） | 不要         |
| `POST`   | `/auth/register`          | ログインユーザーの登録           | 不要         |
| `POST`   | `/auth/token`             | ログインとJWTアクセストークン発行 | 不要         |

プレイヤー作成リクエストの例：

```json
{
  "name": "Cindy"
}
```

作成時の初期スコアは`0`です。クライアントから任意の初期スコアを指定することはできません。

スコア追加リクエストの例：`{"points": 30}`

`points`には0以上の整数を指定します。負数を指定した場合は`422 Unprocessable Content`を返します。

スコア移動リクエストの例：`{"sender": "Alice", "receiver": "Bob", "points": 30}`

`points`には1以上の整数を指定します。送信者と受信者には異なるプレイヤーを指定する必要があります。

プレイヤー名は、前後の空白を除去した後、1文字以上50文字以下である必要があります。

移動履歴のページング例：

```text
GET /transfers?limit=20&offset=0
```

`limit`は1以上100以下で、デフォルトは20です。`offset`は0以上で、デフォルトは0です。

## セットアップ

### 1. 仮想環境の作成

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS／Linux：

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. 依存パッケージのインストール

```bash
python -m pip install -r requirements.txt
```

### 3. APIの起動

```bash
python -m uvicorn main:app --reload
```

起動後、以下からSwagger UIを確認できます。

```text
http://127.0.0.1:8000/docs
```

`/health`以外のプレイヤー関連APIを確認するには、PostgreSQLの起動、環境変数の設定、およびテーブルの作成が必要です。

## PostgreSQLの設定

### 1. 環境変数ファイルの作成

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

macOS／Linux：

```bash
cp .env.example .env
```

作成した`.env`に、自分のPostgreSQL接続情報を設定します。

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=game_player_service
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

`.env`はGitの追跡対象外です。実際のパスワードや接続情報をGitHubへ登録しないでください。

### 2. データベースの作成

通常利用用と統合テスト用の2つを作成します。

```sql
CREATE DATABASE game_player_service;
CREATE DATABASE game_player_service_test;
```

### 3. マイグレーションの実行

`.env`の`DB_NAME`で指定した通常利用用データベースに、最新のマイグレーションを適用します。

```powershell
python -m alembic upgrade head
```

統合テストの開始時には、`migrated_test_database` fixtureが接続先を`game_player_service_test`へ切り替え、同じマイグレーションを自動的に適用します。ホスト、ポート、ユーザー、パスワードには`.env`の設定を使用します。

> [!WARNING]
> 統合テストは`game_player_service_test`内の`transfer_history`、`players`、`users`のデータをテスト前後に削除します。また、Redisを使用するテストは`ranking`キャッシュキーを削除します。テスト用データベースや共有Redisに重要なデータを保存しないでください。

## テスト

PostgreSQLを使用しないコンポーネントテストとAPIテスト：

```bash
python -m pytest -m "not integration" -q
```

実行結果：

```text
169 passed
```

PostgreSQL・Redisを使用するRepository・API統合テスト：

```bash
python -m pytest -m integration -q
```

実行結果：

```text
81 passed
```

全テスト：

```bash
python -m pytest -q
```

現在の実行結果：

```text
250 passed
```

統合テストには、意図的にPostgreSQLの整数上限超過を発生させるテストが含まれています。スコアの加算処理が途中で失敗した場合でも、送信者の減算、受信者の加算、移動履歴の追加がすべてロールバックされることを確認しています。

## GitHub ActionsによるCI

`.github/workflows/ci.yml`により、pushおよびpull requestのたびに次の処理を自動実行します。

* `component-tests`：PostgreSQLを使用しない169件のテスト
* `integration-tests`：PostgreSQL 17の起動、Alembicマイグレーション、81件の統合テスト
* `docker-build`：DockerfileからAPIイメージを構築できることの確認

## プロジェクト構成

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   ├── health.py
│   ├── players.py
│   └── transfers.py
├── migrations/
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 019dd3348d7e_create_players_and_transfer_history_.py
│       ├── 8823f987778c_add_transfer_history_foreign_key_indexes.py
│       ├── b0aae66c3618_create_users_table.py
│       ├── 6c3a3c901882_add_player_ownership.py
│       └── f945c9de2bd9_add_user_roles.py
├── main.py
├── app_factory.py
├── dependencies.py
├── schemas.py
├── exception_handlers.py
├── player_service.py
├── player_repository.py
├── player_repository_protocol.py
├── player_exceptions.py
├── user_service.py
├── user_repository.py
├── user_repository_protocol.py
├── user_exceptions.py
├── manage_users.py
├── password_hasher.py
├── password_hasher_protocol.py
├── token_service.py
├── token_service_protocol.py
├── ranking_cache.py
├── ranking_cache_protocol.py
├── database.py
├── alembic.ini
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .env.example
├── test_main.py
├── test_main_integration.py
├── test_app_factory.py
├── test_authorization.py
├── test_auth_router.py
├── test_auth_integration.py
├── test_player_service.py
├── test_player_repository.py
├── test_user_service.py
├── test_user_repository.py
├── test_user_schemas.py
├── test_manage_users.py
├── test_manage_users_integration.py
├── test_password_hasher.py
├── test_token_service.py
├── test_ranking_cache.py
├── test_dependencies.py
├── test_exception_handlers.py
├── test_health_router.py
├── test_settings.py
├── test_database.py
├── test_migrations.py
├── test_legacy_player_service.py
├── conftest.py
├── pytest.ini
├── requirements.txt
├── IT_LEARNING_REPORT_JA.md
└── README.md
```

## 設計上のポイント

### Repository契約と実装

`PlayerRepositoryProtocol`は、PlayerServiceが必要とするRepositoryメソッドを定義します。通常の実行時には`PlayerRepository`がPostgreSQLへアクセスし、Service単体テストでは`FakeRepository`が同じ契約を満たします。旧トップレベル関数はプライベートな実装補助関数とし、外部コードは`PlayerRepository`の公開メソッドを使用します。

### Service層と依存関係の差し替え

FastAPIのendpointはRepositoryを直接呼び出さず、PlayerServiceを経由します。API単体テストではFakeService、Service単体テストではFakeRepositoryを使用し、PostgreSQL統合テストでは実際のRepositoryとテストデータベースを使用します。

### アプリケーション組み立てとルーティング

`app_factory.py`の`create_app()`がFastAPIアプリケーションを生成し、`main.py`はUvicorn起動用の`app`を公開します。`routers/health.py`、`routers/players.py`、`routers/transfers.py`は関連するendpointを分担し、`dependencies.py`が通常実行時のPlayerRepositoryとPlayerServiceを生成します。各RouterにはSwagger上の表示グループも設定しています。
各Routerは成功時の処理に集中し、PlayerServiceから送出された業務例外は`exception_handlers.py`が一括してHTTPレスポンスへ変換します。

### トランザクションの原子性

スコア移動では、以下の3つを1つのトランザクションとして処理します。

1. 送信者のスコアを減らす
2. 受信者のスコアを増やす
3. `transfer_history`へ履歴を追加する

途中でデータベース例外が発生した場合は、すべての変更をロールバックします。

### データベースマイグレーション

Alembicを使用して、PostgreSQLのテーブル構造をバージョン管理しています。最初のマイグレーションでは`players`と`transfer_history`を作成し、2番目では外部キー列にインデックスを追加しました。3番目ではログインユーザーを保存する`users`テーブルを作成し、4番目では`players.owner_user_id`と外部キー・UNIQUE制約を追加しました。5番目では`users.role`を追加し、初期値を`user`として、`user`または`admin`だけを許可するCHECK制約を設定しています。

新しいデータベースには`alembic upgrade head`で最新構造を作成します。既に同じ構造を持つ開発データベースには`alembic stamp head`を使用し、テーブルを再作成せずに現在のバージョンだけを登録しました。統合テストでは、テスト開始時に最新のマイグレーションを自動適用します。

### 環境設定の一元管理

`pydantic-settings`を使用して、PostgreSQLとRedisの接続設定を環境変数または`.env`から読み込み、必須項目とポート番号の範囲を検証しています。`DB_PASSWORD`は`SecretStr`で通常の表示時にマスクし、`get_settings()`によって検証済みの設定をキャッシュします。Redisには0.5秒の接続・読み書きタイムアウトを設定し、キャッシュ障害時に早くPostgreSQLへ切り替えられるようにしています。

### 同時更新への対応

対象プレイヤーを`SELECT ... FOR UPDATE`でロックします。また、`player_id`順にロックを取得することで、異なるトランザクション間のデッドロックリスクを低減しています。

### 明確な業務結果

スコア移動では、Repositoryが`TransferResult` Enumを返し、PlayerServiceが成功データまたは`PlayerNotFoundError`、`InsufficientScoreError`、`InvalidTransferError`、`UnexpectedTransferResultError`などの業務例外へ変換します。

`exception_handlers.py`は業務例外を一括して`400`、`404`、`409`、`422`、`500`のHTTPレスポンスへ変換します。未定義の技術例外については、詳細とtracebackをサーバーログに記録し、クライアントには内部情報を含まない`{"detail": "Internal server error"}`を返します。

### テスト設計

正常系だけでなく、次のような境界値・異常系もテストしています。

* 空白のプレイヤー名
* 存在しないプレイヤー
* 自分自身へのスコア移動
* 負数および0ポイント
* 残高不足
* 全ポイントの移動
* SQLインジェクション形式の入力
* 同点ランキング
* トランザクション途中のデータベース例外

### Redisランキングキャッシュ

ランキング取得では、最初にRedisを確認し、キャッシュがない場合だけPostgreSQLから取得して60秒間保存します。プレイヤーの作成・削除・スコア追加・スコア移動が成功した場合は、古くなったランキングキャッシュを削除します。

Redisへの接続、読み取り、書き込み、削除に失敗した場合や、キャッシュされたJSONが不正な場合でも、PostgreSQLの処理を継続します。Redisクライアントの自動再試行は無効にし、キャッシュ障害によってAPIが長時間待機しないようにしています。

### APIの入力・出力契約

Pydanticを使用して、プレイヤー名の空白除去・文字数制限、スコアとページングパラメータの範囲、スコア移動時の送信者と受信者が異なることを検証しています。

また、すべての成功レスポンスにレスポンスモデルを設定し、FastAPIが返却データを検証するとともに、Swaggerに明確なAPI仕様を表示します。

### ユーザー認証・所有権・ロール認可

`POST /auth/register`でログインユーザーを登録できます。パスワードはPydanticの`SecretStr`で通常表示から保護し、UserServiceでArgon2ハッシュへ変換してから`users`テーブルに保存します。平文パスワードとパスワードハッシュはAPIレスポンスに含めません。

`POST /auth/token`はOAuth2のパスワードフォームでユーザー名とパスワードを受け取り、Argon2で保存済みパスワードハッシュを検証します。認証に成功した場合は、有効期限付きのJWTアクセストークンを発行します。JWTにはユーザー名を表す`sub`と有効期限`exp`を保存し、パスワードやロールは含めません。

プレイヤー作成時には、JWT認証から特定した現在のログインユーザーの`user_id`を`players.owner_user_id`へ自動的に保存します。クライアントから`owner_user_id`を指定することはできません。外部キーにより実在するユーザーだけを所有者にでき、UNIQUE制約により1ユーザーが所有できるプレイヤーを1件に制限しています。既存データとの互換性のため、未紐付けのプレイヤーでは`owner_user_id`を`NULL`にできます。

`users.role`には`user`または`admin`を保存します。公開登録で作成されるユーザーは必ず`user`となり、クライアントが登録リクエストで`role`を指定した場合は`422`を返します。認証時にはJWTのユーザー名を基にデータベースから最新のユーザー情報とロールを取得します。

プレイヤー作成は認証済みユーザーに許可し、スコア追加は管理者だけに許可します。プレイヤー削除は所有者本人または管理者が実行でき、スコア移動は送信元プレイヤーの所有者本人だけが実行できます。管理者であっても、所有していないプレイヤーになりすましてスコアを移動することはできません。読み取りAPIは公開しています。認証情報が無効な場合は`401`、認証済みでも権限が不足する場合は`403`を返します。

### 管理者ロールの運用

公開登録では一般ユーザーだけを作成します。既存ユーザーを管理者へ昇格する場合は、公開APIではなく、信頼された運用者だけが実行できる`manage_users.py`を使用します。

```powershell
python manage_users.py promote-admin <username>
```

このCLIはUserServiceとUserRepositoryを通して対象ユーザーのロールを`admin`へ更新します。存在しないユーザーを指定した場合はエラーとして終了します。Railway環境ではAPIサービスのConsoleから実行できるため、データベースを直接編集する必要はありません。


## Docker Composeによる実行

`compose.yaml`を使用して、FastAPI、PostgreSQL、Redis、Alembicマイグレーションをまとめて起動できます。

```powershell
docker compose up --build -d
docker compose ps -a
```

起動時にはPostgreSQLとRedisのヘルスチェックを待ちます。次にマイグレーション用コンテナが`alembic upgrade head`を実行し、正常終了した後にFastAPIコンテナを起動します。マイグレーション用コンテナの`Exited (0)`は正常終了を表します。

起動後、次のURLを確認できます。

* ヘルスチェック：`http://localhost:8000/health`
* Swagger UI：`http://localhost:8000/docs`

FastAPIとマイグレーション用コンテナは、実行時に`.env`からデータベース設定を受け取ります。コンテナ内の`DB_HOST`はComposeのサービス名である`db`に上書きされます。PostgreSQLのポートはホストへ公開せず、Compose内部のネットワークからのみ接続します。

PostgreSQLのデータは`postgres_data`というDocker Volumeに保存されるため、次のコマンドでコンテナを削除してもデータは保持されます。

```powershell
docker compose down
```

`docker compose down -v`を実行するとVolumeとデータも削除されるため、必要なデータがある場合は使用しないでください。

Dockerイメージでは不要なファイルと`.env`を除外し、アプリケーションを非rootユーザーの`appuser`で実行します。また、Dockerの`HEALTHCHECK`で`/health`を定期的に確認します。

## Railwayによる公開デプロイ

本プロジェクトはRailwayへデプロイし、ポートフォリオ用の公開デモとして動作しています。

* API：https://game-player-service-production.up.railway.app/
* Swagger UI：https://game-player-service-production.up.railway.app/docs

Railway上では、FastAPI、PostgreSQL、Redisをそれぞれ独立したサービスとして構成しています。外部公開するのはFastAPIサービスだけで、PostgreSQLとRedisはRailwayのプライベートネットワーク内からのみ接続します。

PostgreSQLの接続情報はRailwayの参照変数から受け取り、Redisは`REDIS_URL`が設定されている場合にURL接続を使用します。ローカル環境では従来どおり`REDIS_HOST`と`REDIS_PORT`へフォールバックできます。データベースパスワードとJWT秘密鍵は環境変数として管理し、Gitリポジトリには保存しません。

DockerコンテナはRailwayから渡される`PORT`を使用してUvicornを起動し、ローカル実行時にはポート8000を使用します。デプロイ前には`python -m alembic upgrade head`を実行して最新のマイグレーションを適用し、`/health`によるヘルスチェックが成功した後にデプロイを完了します。また、GitHub ActionsのCIが成功した場合だけ`main`ブランチを自動デプロイするように設定しています。

公開環境では、ユーザー登録、JWTログイン、プレイヤー作成、管理者CLI、ロール・所有権認可、PostgreSQLへの保存、Redisランキングキャッシュと更新時のキャッシュ削除まで確認しています。デモ環境のデータは予告なく変更または削除する場合があります。


## 現在の制約

* 管理者への昇格は信頼された運用者がCLIから実行します。管理画面、管理者ロールの解除、ロール変更の監査ログは未実装です。
* 公開登録にはメールアドレス確認、パスワード再設定、レート制限が未実装です。
* Railwayへの公開デプロイは完了していますが、本番運用を想定した監視・通知、バックアップ復旧手順、高可用性構成は未整備です。
* 本プロジェクトは開発中のポートフォリオであり、完成済みの商用ゲームサーバーを目的としたものではありません。

## 今後の予定

* 公開APIのレート制限とアカウント運用機能の追加
* 管理者操作の監査ログと運用手順の整備
* 監視・通知およびバックアップ復旧手順の整備



---

## 中文说明
[日本語](#game-player-service) | **简体中文**
### 项目简介

Game Player Service 是一个以游戏玩家管理为场景的 Python 后端作品集项目，用于实践 FastAPI、PostgreSQL、Redis、JWT身份认证、所有权与角色授权、pytest自动化测试、Docker和Railway部署。

项目已经实现用户注册与登录、玩家管理、管理员积分发放、玩家间积分转移、转移历史和Redis排行榜缓存等功能。

### 在线演示

* API：https://game-player-service-production.up.railway.app/
* Swagger UI：https://game-player-service-production.up.railway.app/docs

> [!IMPORTANT]
> 当前FastAPI、Service层、PostgreSQL Repository和Redis缓存已经连接，并在Railway上公开运行包含JWT认证、所有权和角色授权的完整API。
> 原内存版Service作为`legacy_player_service.py`保留，用于展示基础业务逻辑和JSON保存功能。


### 当前架构

| 层级                    | 主要职责                          | 主要连接目标                      |
| --------------------- | ----------------------------- | --------------------------- |
| FastAPI API / Router  | HTTP请求与响应、Pydantic输入验证、获取依赖对象 | PlayerService / UserService |
| Service               | 玩家与认证用例、业务结果与业务异常、所有权和角色授权    | Repository Protocol         |
| PostgreSQL Repository | 玩家、用户和积分转移历史的SQL与事务处理         | PostgreSQL                  |
| Redis Ranking Cache   | 排行榜读取缓存、TTL、数据更新时失效、故障时降级     | Redis                       |
| 管理CLI                 | 将现有用户提升为管理员角色                 | UserService                 |
| Legacy PlayerService  | 基础业务逻辑、JSON保存与读取              | 内存／JSON                     |

当前正式API的主要调用路径如下：

* 普通处理：HTTP → FastAPI Router → Service → Repository → Psycopg → PostgreSQL
* 排行榜查询：PlayerService → RedisRankingCache；只有缓存未命中时才通过PlayerRepository访问PostgreSQL
* 身份认证：Bearer Token → `get_current_user` → JWT验证 → UserRepository读取最新用户信息和角色


### 核心功能

* 创建、查询和删除玩家
* 清理玩家名前后的空格
* 拒绝空白名和重复玩家名
* 为玩家增加非负积分
* 按积分降序生成排行榜
* 同分时按玩家名升序排序
* 在玩家之间转移积分
* 保存积分转移历史
* 使用 JSON 保存和读取内存数据
* 使用 PostgreSQL 保存玩家和转移记录
* 使用参数化 SQL 防止输入被解释为 SQL
* 使用数据库约束保护数据合法性
* 使用事务保证积分转移的原子性
* 使用 pytest 执行自动化测试

### 技术栈

* Python 3.11
* FastAPI
* Pydantic
* pydantic-settings
* Uvicorn
* PostgreSQL
* Psycopg 3
* SQLAlchemy
* Alembic
* python-dotenv
* pytest
* HTTPX2
* Git
* Docker
* GitHub Actions
* Docker Compose
* Redis
* redis-py
* pwdlib
* Argon2
* PyJWT
* pwdlib / Argon2
* Railway

### 当前 API

玩家信息保存在 PostgreSQL 的 `players` 表中。FastAPI 启动时不会自动创建示例玩家。

| Method   | Endpoint                  | 说明                     | 认证         |
|----------|---------------------------|--------------------------|--------------|
| `GET`    | `/health`                 | 健康检查                 | 无需         |
| `GET`    | `/players/{name}`         | 查询玩家                 | 无需         |
| `GET`    | `/ranking`                | 获取排行榜               | 无需         |
| `POST`   | `/players`                | 创建玩家                 | Bearer Token |
| `DELETE` | `/players/{name}`         | 删除玩家                 | Bearer Token |
| `PATCH`  | `/players/{name}/score`   | 增加积分                 | Bearer Token |
| `POST`   | `/transfers`              | 转移积分                 | Bearer Token |
| `GET`    | `/transfers`              | 查询转移历史（支持分页） | 无需         |
| `POST`   | `/auth/register`          | 注册登录用户             | 无需         |
| `POST`   | `/auth/token`             | 登录并签发JWT访问令牌    | 无需         |

创建玩家的请求示例：

```json
{
  "name": "Cindy"
}
```

玩家创建后的初始积分固定为 `0`，请求方不能指定任意初始积分。

增加积分请求示例：`{"points": 30}`

`points` 必须是大于或等于 0 的整数。传入负数时返回 `422 Unprocessable Content`。

积分转移请求示例：`{"sender": "Alice", "receiver": "Bob", "points": 30}`

`points` 必须是大于或等于 1 的整数，发送者和接收者必须是不同玩家。

玩家名去除首尾空格后，长度必须为1～50个字符。

转移历史分页示例：

```text
GET /transfers?limit=20&offset=0
```

`limit`的范围是1～100，默认值为20；`offset`必须大于或等于0，默认值为0。

### 快速运行 API

创建并激活虚拟环境后安装依赖：

```bash
python -m pip install -r requirements.txt
```

启动服务：

```bash
python -m uvicorn main:app --reload
```

Swagger API 文档地址：

```text
http://127.0.0.1:8000/docs
```

除 `/health` 外，使用玩家相关 API 前需要启动 PostgreSQL、配置环境变量并创建数据库表。

### PostgreSQL 配置

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

在创建的 `.env` 中填写自己的 PostgreSQL 连接信息：

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=game_player_service
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

`.env` 已被 Git 忽略，请勿把真实密码或数据库连接信息提交到 GitHub。

### 2. 创建数据库

需要创建普通开发和集成测试使用的两个数据库：

```sql
CREATE DATABASE game_player_service;
CREATE DATABASE game_player_service_test;
```

### 3. 执行数据库迁移

对 `.env` 的 `DB_NAME` 指定的普通开发数据库执行最新迁移：

```powershell
python -m alembic upgrade head
```

项目使用Alembic对PostgreSQL表结构进行版本管理。第一份迁移创建`players`和`transfer_history`，第二份迁移为外键列添加索引，第三份迁移创建保存登录用户的`users`表，第四份迁移添加`players.owner_user_id`及其外键和UNIQUE约束，第五份迁移添加`users.role`，默认值为`user`，并通过CHECK约束只允许`user`或`admin`。

集成测试开始时，`migrated_test_database` fixture 会把连接目标切换到 `game_player_service_test`，并自动执行相同的数据库迁移。主机、端口、用户名和密码继续使用 `.env` 中的配置。迁移链还会依次创建用户表、添加玩家所有权，并添加普通用户与管理员角色。

> [!WARNING]
> 集成测试会在测试前后清空`game_player_service_test`中的`transfer_history`、`players`和`users`表。使用Redis的测试还会删除`ranking`缓存键。请勿在测试数据库或共享Redis中保存重要数据。

### 自动化测试

不需要 PostgreSQL 的组件测试和 API 测试：

```bash
python -m pytest -m "not integration" -q
```

当前结果：

```text
169 passed
```

使用 PostgreSQL 与 Redis 的 Repository/API 集成测试：

```bash
python -m pytest -m integration -q
```

当前结果：

```text
81 passed
```

执行全部测试：

```bash
python -m pytest -q
```

当前结果：

```text
250 passed
```

### GitHub Actions CI

`.github/workflows/ci.yml` 会在每次 push 和 pull request 时自动执行：

* `component-tests`：运行不需要 PostgreSQL 的169个测试
* `integration-tests`：启动 PostgreSQL 17、执行 Alembic 迁移并运行81个集成测试
* `docker-build`：确认能够通过 Dockerfile 成功构建 API 镜像

### 事务设计

数据库版积分转移会在同一个事务中完成以下三项操作：

1. 扣除发送者的积分
2. 增加接收者的积分
3. 写入 `transfer_history`

目标玩家会通过 `SELECT ... FOR UPDATE` 加行锁，并按照 `player_id` 的固定顺序申请锁，以降低并发事务发生死锁的风险。

测试中还会故意让接收者积分超过 PostgreSQL `integer` 的上限，使第二次更新触发 `NumericValueOutOfRange`。测试确认异常发生后：

* 发送者已执行的扣分会被回滚
* 接收者积分保持不变
* 不会留下转移历史

这不是仅根据代码推测事务原子性，而是通过真实数据库故障注入进行验证。

### Repository 契约与实现

`PlayerRepositoryProtocol` 定义了 PlayerService 所需的 Repository 方法。正常运行时由 `PlayerRepository` 访问 PostgreSQL；Service 单元测试中由 `FakeRepository` 满足同一份契约。原先的顶层函数已改为私有实现辅助函数，外部代码应使用 `PlayerRepository` 的公开方法。

### 明确的业务结果

积分转移时，Repository 返回`TransferResult` Enum，PlayerService 将其转换为成功数据，或`PlayerNotFoundError`、`InsufficientScoreError`、`InvalidTransferError`、`UnexpectedTransferResultError`等业务异常。

`exception_handlers.py` 统一把业务异常转换为`400`、`404`、`409`、`422`、`500`等 HTTP 响应。对于未定义的技术异常，系统会把详细信息和 traceback 写入服务器日志，同时只向客户端返回不包含内部信息的`{"detail": "Internal server error"}`。

### 集中管理环境配置

项目使用 `pydantic-settings` 从环境变量或 `.env` 读取 PostgreSQL 与 Redis 的连接配置，并验证必填项和端口范围。`DB_PASSWORD` 使用 `SecretStr` 在普通输出中隐藏密码，`get_settings()` 会缓存已经验证的配置。Redis 设置了0.5秒的连接与读写超时，以便缓存故障时尽快切换到 PostgreSQL。

### 数据库迁移

项目使用 Alembic 对 PostgreSQL 表结构进行版本管理。第一份迁移负责创建 `players` 和 `transfer_history`，并定义外键、CHECK 约束和 UNIQUE 约束。

新数据库通过 `alembic upgrade head` 创建最新结构。对于已经具有相同结构的开发数据库，使用 `alembic stamp head` 只登记当前版本，不重复创建数据表。集成测试会在开始时自动应用最新迁移。

### Service 层与依赖替换

FastAPI endpoint 不再直接调用 Repository，而是通过 PlayerService 执行业务流程。API 单元测试使用 FakeService，Service 单元测试使用 FakeRepository，PostgreSQL 集成测试则使用真实 Repository 和测试数据库。

### 应用组装与路由

`app_factory.py` 中的 `create_app()` 负责创建 FastAPI 应用，`main.py` 只公开供 Uvicorn 启动的 `app`。`routers/health.py`、`routers/players.py` 和 `routers/transfers.py` 分别负责相关接口，`dependencies.py` 在正常运行时创建 PlayerRepository 和 PlayerService。各 Router 也配置了 Swagger 中的接口分组。
各 Router 只处理成功流程，PlayerService 抛出的业务异常统一由 `exception_handlers.py` 转换为 HTTP 响应。

### Redis 排行榜缓存

查询排行榜时会先检查 Redis，只有缓存不存在时才从 PostgreSQL 获取数据，并保存60秒。创建或删除玩家、增加积分、转移积分成功后，会删除已经过期的排行榜缓存。

Redis 连接、读取、写入或删除失败，以及缓存中的 JSON 无效时，系统仍会继续使用 PostgreSQL。Redis 客户端的自动重试已关闭，避免缓存故障导致 API 长时间等待。

### API 输入与输出契约

项目使用 Pydantic 检查玩家名的首尾空格和长度、积分与分页参数的范围，以及积分转移时发送者和接收者不能相同。

所有成功响应都配置了响应模型，使 FastAPI 能在返回前检查数据结构，并在 Swagger 中生成明确的 API 说明。

### 用户认证、所有权与角色授权

可以通过`POST /auth/register`注册登录用户。密码首先由Pydantic的`SecretStr`避免在普通输出中暴露，再由UserService转换为Argon2哈希后保存到`users`表。API响应不会包含明文密码或密码哈希。

`POST /auth/token`通过OAuth2密码表单接收用户名和密码，并使用Argon2验证数据库中保存的密码哈希。认证成功后，接口签发带有效期的JWT访问令牌。JWT只保存表示用户名的`sub`和过期时间`exp`，不会包含密码或用户角色。

创建玩家时，系统会将通过JWT认证得到的当前登录用户`user_id`自动写入`players.owner_user_id`，客户端不能自行指定`owner_user_id`。外键保证所有者必须是真实存在的用户，UNIQUE约束将每个用户可拥有的玩家限制为一个。为了兼容已有数据，尚未绑定用户的旧玩家可以将`owner_user_id`保留为`NULL`。

`users.role`保存`user`或`admin`。通过公开注册接口创建的用户固定为`user`，客户端在注册请求中提交`role`时会得到`422`。身份认证时，系统根据JWT中的用户名重新从数据库读取最新的用户信息和角色。

创建玩家允许所有已认证用户执行，增加积分仅允许管理员执行。删除玩家只允许玩家所有者本人或管理员执行，转移积分只允许发送方玩家的所有者本人执行。即使是管理员，也不能冒充自己不拥有的玩家转移积分。读取API保持公开。身份认证失败时返回`401`，身份有效但权限不足时返回`403`。

### 管理员角色运维

公开注册接口只会创建普通用户。需要将现有用户提升为管理员时，不使用公开API，而是由可信的服务器运维人员执行`manage_users.py`。

```powershell
python manage_users.py promote-admin <username>
```

该CLI通过UserService和UserRepository将目标用户的角色更新为`admin`。如果指定的用户不存在，命令会以错误结束。在Railway环境中可以从API服务的Console执行，因此不需要直接编辑数据库。


### 测试覆盖的代表场景

* 玩家名为空或仅包含空格
* 玩家名重复
* 玩家不存在
* SQL 注入形式的输入
* 负数积分
* 0 积分
* 余额不足
* 将全部积分转出
* 向自己转移积分
* 排行榜同分排序
* 转移记录保存
* 数据库更新途中发生异常
* 事务整体回滚

### 使用 Docker Compose 运行

通过`compose.yaml`可以统一启动FastAPI、PostgreSQL、Redis和Alembic迁移服务。

```powershell
docker compose up --build -d
docker compose ps -a
```

启动时会等待PostgreSQL和Redis通过健康检查，然后由迁移容器执行`alembic upgrade head`。迁移成功结束后，FastAPI容器才会启动。迁移容器显示`Exited (0)`代表正常完成，并不是故障。
启动后可以访问：

* 健康检查：`http://localhost:8000/health`
* Swagger UI：`http://localhost:8000/docs`

FastAPI和迁移容器会在运行时读取`.env`中的数据库配置，并将容器内的`DB_HOST`覆盖为Compose服务名`db`。PostgreSQL端口不会发布到宿主机，只允许Compose内部网络中的服务访问。

PostgreSQL数据保存在名为`postgres_data`的Docker Volume中，因此执行下面的命令删除容器后，数据仍然保留：

```powershell
docker compose down
```

`docker compose down -v`会同时删除Volume和数据库数据，存在需要保留的数据时不要使用。

Docker镜像会排除无关文件和`.env`，并使用非root用户`appuser`运行应用。Docker的`HEALTHCHECK`会定期访问`/health`检查API状态。

### Railway公开部署

本项目已经部署到Railway，并作为作品集公开演示环境运行。

* API：https://game-player-service-production.up.railway.app/
* Swagger UI：https://game-player-service-production.up.railway.app/docs

Railway中分别运行FastAPI、PostgreSQL和Redis三个独立服务。只有FastAPI服务对外公开，PostgreSQL与Redis只能通过Railway内部私有网络访问。

PostgreSQL连接信息通过Railway服务引用变量传入。设置`REDIS_URL`时，应用使用URL连接Redis；在本地环境中则可以继续使用`REDIS_HOST`和`REDIS_PORT`作为后备配置。数据库密码与JWT密钥均通过环境变量管理，不会保存到Git仓库。

Docker容器使用Railway提供的`PORT`启动Uvicorn，本地运行时则默认使用8000端口。部署前会执行`python -m alembic upgrade head`应用最新数据库迁移，并通过`/health`健康检查确认API已经正常启动。项目还配置为只有GitHub Actions CI成功后，才自动部署`main`分支。

已经在公开环境中验证了用户注册、JWT登录、玩家创建、管理员CLI、角色与所有权授权、PostgreSQL持久化、Redis排行榜缓存，以及数据更新后的缓存失效。演示环境中的数据可能在不提前通知的情况下被修改或清理。


### 当前限制

* 管理员提升由可信的运维人员通过CLI执行，尚未实现管理页面、取消管理员角色和角色变更审计日志
* 公开注册尚未实现邮箱验证、密码重置和请求速率限制
* 已完成Railway公开部署，但尚未建立面向正式生产环境的监控告警、备份恢复流程和高可用架构
* 当前项目是持续开发中的作品集，不以成为完整的商业游戏服务器为目标

### 后续计划

* 为公开API增加速率限制与账户运维功能
* 增加管理员操作审计日志并完善运维流程
* 完善监控告警与备份恢复流程
