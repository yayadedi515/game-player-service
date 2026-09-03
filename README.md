# Game Player Service

[![CI](https://github.com/yayadedi515/game-player-service/actions/workflows/ci.yml/badge.svg)](https://github.com/yayadedi515/game-player-service/actions/workflows/ci.yml)

**日本語** | [简体中文](#中文说明)

プレイヤー管理を題材に、FastAPI、PostgreSQL、トランザクション処理、pytestによる自動テストを実践したPythonバックエンドのポートフォリオです。

プレイヤーの作成・検索・削除、スコア管理、ランキング、プレイヤー間のスコア移動、移動履歴などを実装しています。

> [!IMPORTANT]
> 現在、FastAPI、PlayerService、PostgreSQL Repositoryが接続されており、プレイヤーの作成・検索・削除・スコア追加・スコア移動・移動履歴取得・ランキング取得をPostgreSQL上で実行できます。
> 旧インメモリ版のServiceは、基礎的な業務ロジックとJSON保存を確認する`legacy_player_service.py`として残しています。

## 現在の構成

| レイヤー                  | 主な機能                                      | データ保存先       |
|------------------------|-------------------------------------------|--------------|
| FastAPI API / Router   | HTTPリクエスト・レスポンス、入力検証、グローバル例外変換 | PlayerService経由 |
| PlayerService          | APIユースケースの調整、Repository契約に基づく業務結果・業務例外への変換 | PlayerRepositoryProtocol経由 |
| PostgreSQL Repository  | PlayerRepositoryクラス、SQL、トランザクション、PostgreSQLデータアクセス | PostgreSQL |
| Legacy PlayerService   | 基礎的な業務ロジック、JSON保存・読込                     | メモリ／JSON       |

現在の正式なAPI経路は次のとおりです。

```text
HTTP → FastAPI → PlayerService → PostgreSQL Repository → Psycopg → PostgreSQL
```

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

## API

プレイヤー情報はPostgreSQLの`players`テーブルに保存されます。FastAPI起動時にサンプルプレイヤーは自動登録されません。

| Method   | Endpoint          | 説明       |
| -------- | ----------------- | -------- |
| `GET`    | `/health`         | ヘルスチェック  |
| `GET`    | `/players/{name}` | プレイヤーの取得 |
| `GET`    | `/ranking`        | ランキングの取得 |
| `POST`   | `/players`        | プレイヤーの作成 |
| `DELETE` | `/players/{name}` | プレイヤーの削除 |
| `PATCH`  | `/players/{name}/score` | スコアの追加 |
| `POST`   | `/transfers`             | スコアの移動 |
| `GET`    | `/transfers`             | 移動履歴の取得（ページング対応） |

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
> 統合テストは`game_player_service_test`内の`players`と`transfer_history`のデータをテスト前後に削除します。重要なデータを保存しないでください。

## テスト

PostgreSQLを使用しないコンポーネントテストとAPIテスト：

```bash
python -m pytest -m "not integration" -q
```

実行結果：

```text
91 passed
```

PostgreSQL Repository・API統合テスト：

```bash
python -m pytest -m integration -q
```

実行結果：

```text
56 passed
```

全テスト：

```bash
python -m pytest -q
```

現在の実行結果：

```text
146 passed
```

統合テストには、意図的にPostgreSQLの整数上限超過を発生させるテストが含まれています。スコアの加算処理が途中で失敗した場合でも、送信者の減算、受信者の加算、移動履歴の追加がすべてロールバックされることを確認しています。

## GitHub ActionsによるCI

`.github/workflows/ci.yml`により、pushおよびpull requestのたびに次の処理を自動実行します。

* `component-tests`：PostgreSQLを使用しない91件のテスト
* `integration-tests`：PostgreSQL 17の起動、Alembicマイグレーション、56件の統合テスト
* `docker-build`：DockerfileからAPIイメージを構築できることの確認

## プロジェクト構成

```text
.
├── Dockerfile
├── .dockerignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── main.py
├── compose.yaml
├── app_factory.py
├── dependencies.py
├── routers/
│   ├── __init__.py
│   ├── health.py
│   ├── players.py
│   └── transfers.py
├── schemas.py
├── player_service.py
├── legacy_player_service.py
├── player_exceptions.py
├── player_repository_protocol.py
├── player_repository.py
├── exception_handlers.py
├── settings.py
├── database.py
├── alembic.ini
├── migrations/
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 019dd3348d7e_create_players_and_transfer_history_.py
│       └── 8823f987778c_add_transfer_history_foreign_key_indexes.py
├── test_main.py
├── test_main_integration.py
├── test_player_service.py
├── test_legacy_player_service.py
├── test_player_repository.py
├── test_app_factory.py
├── test_dependencies.py
├── test_health_router.py
├── test_exception_handlers.py
├── test_settings.py
├── test_database.py
├── test_migrations.py
├── conftest.py
├── pytest.ini
├── requirements.txt
├── .env.example
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

Alembicを使用して、PostgreSQLのテーブル構造をバージョン管理しています。最初のマイグレーションでは`players`と`transfer_history`を作成し、外部キー、CHECK制約、UNIQUE制約も定義しています。2番目のマイグレーションでは、外部キー確認とプレイヤー別履歴検索を効率化するため、送信者IDと受信者IDにインデックスを追加しています。

新しいデータベースには`alembic upgrade head`で最新構造を作成します。既に同じ構造を持つ開発データベースには`alembic stamp head`を使用し、テーブルを再作成せずに現在のバージョンだけを登録しました。統合テストでは、テスト開始時に最新のマイグレーションを自動適用します。

### 環境設定の一元管理

`pydantic-settings`を使用して、PostgreSQLの接続設定を環境変数または`.env`から読み込み、必須項目とポート番号の範囲を検証しています。`DB_PASSWORD`は`SecretStr`で通常の表示時にマスクし、`get_settings()`によって検証済みの設定をキャッシュします。テストではキャッシュを明示的にクリアし、テスト用データベースの設定を分離しています。

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

### APIの入力・出力契約

Pydanticを使用して、プレイヤー名の空白除去・文字数制限、スコアとページングパラメータの範囲、スコア移動時の送信者と受信者が異なることを検証しています。

また、すべての成功レスポンスにレスポンスモデルを設定し、FastAPIが返却データを検証するとともに、Swaggerに明確なAPI仕様を表示します。

## Docker Composeによる実行

`compose.yaml`を使用して、FastAPI、PostgreSQL、Alembicマイグレーションをまとめて起動できます。

```powershell
docker compose up --build -d
docker compose ps -a
```

起動時には、最初にPostgreSQLのヘルスチェックを待ちます。次にマイグレーション用コンテナが`alembic upgrade head`を実行し、正常終了した後にFastAPIコンテナを起動します。マイグレーション用コンテナの`Exited (0)`は正常終了を表します。

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

## 現在の制約

* 認証・認可は未実装です。
* Redisなどのキャッシュは未導入です。
* Docker Composeによる開発用実行環境は構築済みですが、本番環境へのデプロイは未実装です。
* 本プロジェクトは開発中のポートフォリオであり、本番運用を目的とした完成済みシステムではありません。

## 今後の予定

* Redisによるキャッシュの導入
* 認証・認可の実装



---

## 中文说明
[日本語](#game-player-service) | **简体中文**
### 项目简介

Game Player Service 是一个以游戏玩家管理为场景的 Python 后端作品集项目，用于实践 FastAPI、PostgreSQL、数据库事务、自动化测试和 Git 开发流程。

项目已实现玩家创建、查询、删除、积分增加、排行榜、玩家间积分转移、转移历史及 JSON 持久化等功能。

> [!IMPORTANT]
> 当前 FastAPI、PlayerService 和 PostgreSQL Repository 已正式连接，可以使用 PostgreSQL 完成玩家创建、查询、删除、积分增加、积分转移、转移历史查询和排行榜获取。
> 原内存版 Service 作为 `legacy_player_service.py` 保留，用于展示基础业务逻辑和 JSON 保存功能。

### 当前架构

| 层级                    | 主要职责                         | 数据存储       |
|-----------------------|------------------------------|------------|
| FastAPI API / Router  | HTTP 请求与响应、输入验证、全局异常转换 | 通过 PlayerService |
| PlayerService         | 组织 API 用例、基于 Repository 契约转换业务结果与业务异常 | 通过 PlayerRepositoryProtocol |
| PostgreSQL Repository | PlayerRepository 类、SQL、事务及 PostgreSQL 数据访问 | PostgreSQL |
| Legacy PlayerService  | 基础业务逻辑、JSON 保存与读取            | 内存／JSON    |

当前正式 API 的调用路径为：

HTTP → FastAPI → PlayerService → PostgreSQL Repository → Psycopg → PostgreSQL

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

### 当前 API

玩家信息保存在 PostgreSQL 的 `players` 表中。FastAPI 启动时不会自动创建示例玩家。

| 请求方法     | 接口                | 说明    |
| -------- | ----------------- | ----- |
| `GET`    | `/health`         | 健康检查  |
| `GET`    | `/players/{name}` | 查询玩家  |
| `GET`    | `/ranking`        | 获取排行榜 |
| `POST`   | `/players`        | 创建玩家  |
| `DELETE` | `/players/{name}` | 删除玩家  |
| `PATCH`  | `/players/{name}/score` | 增加积分 |
| `POST`   | `/transfers`             | 转移积分 |
| `GET`    | `/transfers`             | 查询转移历史（支持分页） |

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

集成测试开始时，`migrated_test_database` fixture 会把连接目标切换到 `game_player_service_test`，并自动执行相同的数据库迁移。主机、端口、用户名和密码继续使用 `.env` 中的配置。第二份迁移为发送者ID和接收者ID添加索引，以提高外键检查和按玩家查询转移历史时的效率。

> [!WARNING]
> 集成测试会在测试前后清空 `game_player_service_test` 中 `players` 和 `transfer_history` 表内的数据。请勿在该测试数据库中保存重要数据。

### 自动化测试

不需要 PostgreSQL 的组件测试和 API 测试：

```bash
python -m pytest -m "not integration" -q
```

当前结果：

```text
91 passed
```

PostgreSQL Repository 与 API 集成测试：

```bash
python -m pytest -m integration -q
```

当前结果：

```text
56 passed
```

执行全部测试：

```bash
python -m pytest -q
```

当前结果：

```text
146 passed
```

### GitHub Actions CI

`.github/workflows/ci.yml` 会在每次 push 和 pull request 时自动执行：

* `component-tests`：运行不需要 PostgreSQL 的91个测试
* `integration-tests`：启动 PostgreSQL 17、执行 Alembic 迁移并运行56个集成测试
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

项目使用 `pydantic-settings` 从环境变量或 `.env` 读取 PostgreSQL 连接配置，并验证必填项和端口范围。`DB_PASSWORD` 使用 `SecretStr` 在普通输出中隐藏密码，`get_settings()` 会缓存已经验证的配置。测试会显式清除缓存，以隔离测试数据库配置。

### 数据库迁移

项目使用 Alembic 对 PostgreSQL 表结构进行版本管理。第一份迁移负责创建 `players` 和 `transfer_history`，并定义外键、CHECK 约束和 UNIQUE 约束。

新数据库通过 `alembic upgrade head` 创建最新结构。对于已经具有相同结构的开发数据库，使用 `alembic stamp head` 只登记当前版本，不重复创建数据表。集成测试会在开始时自动应用最新迁移。

### Service 层与依赖替换

FastAPI endpoint 不再直接调用 Repository，而是通过 PlayerService 执行业务流程。API 单元测试使用 FakeService，Service 单元测试使用 FakeRepository，PostgreSQL 集成测试则使用真实 Repository 和测试数据库。

### 应用组装与路由

`app_factory.py` 中的 `create_app()` 负责创建 FastAPI 应用，`main.py` 只公开供 Uvicorn 启动的 `app`。`routers/health.py`、`routers/players.py` 和 `routers/transfers.py` 分别负责相关接口，`dependencies.py` 在正常运行时创建 PlayerRepository 和 PlayerService。各 Router 也配置了 Swagger 中的接口分组。
各 Router 只处理成功流程，PlayerService 抛出的业务异常统一由 `exception_handlers.py` 转换为 HTTP 响应。

### API 输入与输出契约

项目使用 Pydantic 检查玩家名的首尾空格和长度、积分与分页参数的范围，以及积分转移时发送者和接收者不能相同。

所有成功响应都配置了响应模型，使 FastAPI 能在返回前检查数据结构，并在 Swagger 中生成明确的 API 说明。

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

通过`compose.yaml`可以统一启动FastAPI、PostgreSQL和Alembic迁移服务。

```powershell
docker compose up --build -d
docker compose ps -a
```

启动时会先等待PostgreSQL通过健康检查，然后由迁移容器执行`alembic upgrade head`。迁移成功结束后，FastAPI容器才会启动。迁移容器显示`Exited (0)`代表正常完成，并不是故障。

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

### 当前限制

* 尚未实现认证和权限控制
* 尚未引入 Redis 等缓存
* 已完成Docker Compose开发环境，但尚未完成线上部署
* 当前是持续开发中的作品集项目，不能视为已经完成的生产级系统

### 后续计划

* 引入 Redis 缓存
* 实现认证和权限控制
