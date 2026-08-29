# Game Player Service
**日本語** | [简体中文](#中文说明)
プレイヤー管理を題材に、FastAPI、PostgreSQL、トランザクション処理、pytestによる自動テストを実践したPythonバックエンドのポートフォリオです。

プレイヤーの作成・検索・削除、スコア管理、ランキング、プレイヤー間のスコア移動、移動履歴などを実装しています。

> [!IMPORTANT]
> 現在、FastAPIはPostgreSQL Repositoryと接続されており、プレイヤーの作成・検索・削除・スコア追加・スコア移動・ランキング取得をPostgreSQL上で実行できます。
> インメモリ版の`PlayerService`は、基礎的な業務ロジックとJSON保存を確認する独立した学習実装として残しています。

## 現在の構成

| レイヤー                  | 主な機能                                            | データ保存先    |
|------------------------|-------------------------------------------------|------------|
| FastAPI API            | プレイヤー作成・検索・削除、スコア追加・移動、ランキング                   | PostgreSQL |
| PlayerService          | スコア追加、スコア移動、履歴、JSON保存・読込                        | メモリ／JSON   |
| PostgreSQL Repository  | プレイヤー検索・作成・削除、スコア追加、ランキング、トランザクション付きスコア移動 | PostgreSQL |

現在の正式なAPI経路は次のとおりです。

```text
HTTP → FastAPI → PostgreSQL Repository → Psycopg → PostgreSQL
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
* Uvicorn
* PostgreSQL
* Psycopg 3
* python-dotenv
* pytest
* HTTPX2
* Git

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

### 3. テーブルの作成

両方のデータベースに`database/schema.sql`を適用します。

```bash
psql -U your_database_user -d game_player_service -f database/schema.sql
psql -U your_database_user -d game_player_service_test -f database/schema.sql
```

Repository統合テストでは、データベース名を自動的に`game_player_service_test`へ切り替えます。ホスト、ポート、ユーザー、パスワードは`.env`の設定を使用します。

> [!WARNING]
> 統合テストは`game_player_service_test`内の`players`と`transfer_history`をテスト前後に削除します。重要なデータを保存しないでください。

## テスト

PostgreSQLを使用しないコンポーネントテストとAPIテスト：

```bash
python -m pytest -m "not integration" -q
```

実行結果：

```text
29 passed
```

PostgreSQL Repository・API統合テスト：

```bash
python -m pytest -m integration -q
```

実行結果：

```text
45 passed
```

全テスト：

```bash
python -m pytest -q
```

現在の実行結果：

```text
74 passed
```

統合テストには、意図的にPostgreSQLの整数上限超過を発生させるテストが含まれています。スコアの加算処理が途中で失敗した場合でも、送信者の減算、受信者の加算、移動履歴の追加がすべてロールバックされることを確認しています。

## プロジェクト構成

```text
.
├── main.py
├── player_service.py
├── player_repository.py
├── database.py
├── database/
│   └── schema.sql
├── test_main.py
├── test_main_integration.py
├── test_player_service.py
├── test_player_repository.py
├── conftest.py
├── pytest.ini
├── requirements.txt
├── .env.example
└── README.md
```

## 設計上のポイント

### トランザクションの原子性

スコア移動では、以下の3つを1つのトランザクションとして処理します。

1. 送信者のスコアを減らす
2. 受信者のスコアを増やす
3. `transfer_history`へ履歴を追加する

途中でデータベース例外が発生した場合は、すべての変更をロールバックします。

### 同時更新への対応

対象プレイヤーを`SELECT ... FOR UPDATE`でロックします。また、`player_id`順にロックを取得することで、異なるトランザクション間のデッドロックリスクを低減しています。

### 明確な業務結果

スコア移動処理では、単純な`True`／`False`ではなく、`TransferResult` Enumを使用しています。成功、プレイヤーが存在しない場合、スコア不足、不正なリクエストを区別し、FastAPIで`201`、`404`、`409`、`422`のHTTPステータスに変換します。

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

## 現在の制約

* 履歴取得は、まだHTTP APIとして公開していません。
* 認証・認可は未実装です。
* Docker化および本番環境へのデプロイは未実装です。
* 本プロジェクトは開発中のポートフォリオであり、本番運用を目的とした完成済みシステムではありません。

## 今後の予定

* 履歴取得APIの実装
* Pydanticによるリクエスト境界の検証強化
* Dockerによる実行環境の構築
* CIによる自動テスト



---

## 中文说明
[日本語](#game-player-service) | **简体中文**
### 项目简介

Game Player Service 是一个以游戏玩家管理为场景的 Python 后端作品集项目，用于实践 FastAPI、PostgreSQL、数据库事务、自动化测试和 Git 开发流程。

项目已实现玩家创建、查询、删除、积分增加、排行榜、玩家间积分转移、转移历史及 JSON 持久化等功能。

> [!IMPORTANT]
> 当前 FastAPI 已正式连接 PostgreSQL Repository，可以使用 PostgreSQL 完成玩家创建、查询、删除、积分增加、积分转移和排行榜获取。
> 内存版 `PlayerService` 作为基础业务逻辑和 JSON 保存功能的独立学习实现保留。

### 当前架构

| 层级                    | 已实现功能                       | 数据存储       |
| --------------------- |-----------------------------| ---------- |
| FastAPI API           | 玩家创建、查询、删除、积分增加、积分转移、排行榜     | PostgreSQL |
| PlayerService         | 积分增加、积分转移、历史记录、JSON 保存与读取   | 内存／JSON    |
| PostgreSQL Repository | 玩家查询、创建、删除、积分增加、排行榜、事务化积分转移 | PostgreSQL |

当前正式 API 的调用路径为：

`HTTP → FastAPI → PostgreSQL Repository → Psycopg → PostgreSQL`

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
* Uvicorn
* PostgreSQL
* Psycopg 3
* python-dotenv
* pytest
* HTTPX2
* Git

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

在本地 `.env` 中填写数据库连接信息：

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=game_player_service
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

需要准备两个数据库：

* `game_player_service`：Repository 的普通开发数据库
* `game_player_service_test`：Repository 集成测试专用数据库

然后分别执行 `database/schema.sql` 创建数据表。

`.env` 已被 Git 忽略，真实密码和数据库连接信息没有提交到公开仓库。

> [!WARNING]
> Repository 集成测试会在测试前后清空 `game_player_service_test` 中的玩家和转移历史。请勿在该测试数据库中保存重要数据。

### 自动化测试

不需要 PostgreSQL 的组件测试和 API 测试：

```bash
python -m pytest -m "not integration" -q
```

当前结果：

```text
29 passed
```

PostgreSQL Repository 与 API 集成测试：

```bash
python -m pytest -m integration -q
```

当前结果：

```text
45 passed
```

执行全部测试：

```bash
python -m pytest -q
```

当前结果：

```text
74 passed
```

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

### 明确的业务结果

积分转移不再只返回`True`／`False`，而是使用`TransferResult` Enum 区分成功、玩家不存在、积分不足和非法请求。FastAPI 再将这些业务结果分别转换为`201`、`404`、`409`和`422`状态码。

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

### 当前限制

* 转移历史查询尚未开放为 HTTP API
* 尚未实现认证和权限控制
* 尚未完成 Docker 化和线上部署
* 当前是持续开发中的作品集项目，不能视为已经完成的生产级系统

### 后续计划

* 实现转移历史查询 API
* 加强 Pydantic 请求边界验证
* 增加 Docker 运行环境
* 使用 CI 自动运行测试
