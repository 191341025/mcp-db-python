# MCP DB Python

MCP DB Python 是一个以 Python 编写的 Model Context Protocol (MCP) 数据库服务，能够通过标准输入/输出上的 JSON-RPC 协议提供安全的数据库结构浏览与查询能力。MCP DB Python is a Python-powered Model Context Protocol (MCP) server that exposes safe database inspection and read-only querying over JSON-RPC via stdin/stdout.

## 项目简介 | Overview

本项目封装了基础的 MCP Server 启动逻辑与数据源适配层，当前聚焦 MySQL，便于在 LLM 工具链中快速调用数据库结构信息与只读查询结果。随着后续维护，接口与数据源适配将持续扩充，帮助更多场景接入 MCP 协议。  
This repository packages the core MCP server loop together with database adapters focused on MySQL, making it straightforward to surface schema metadata and read-only query results inside LLM agent workflows. The API surface and connector set will keep expanding as the project is actively maintained.

## 主要特性 | Key Features

- 面向 MCP 的 JSON-RPC 通信，兼容多种支持 MCP 的客户端 / MCP-compliant JSON-RPC transport ready for compatible clients.
- MySQL 表结构与存储过程元数据查询能力 / Schema and stored procedure introspection for MySQL.
- 严格的只读 SQL 校验，保障在线环境安全 / Strict read-only SQL validation to protect production data.
- 基于 `.env` 的可配置数据源参数，便于跨环境部署 / `.env`-driven connector settings for seamless environment switching.
- 持续维护与扩展，后续将新增更多数据库适配与工具接口 / Actively maintained roadmap toward additional connectors and tools.

## 快速开始 | Quick Start

### 环境要求 | Requirements

- Python 3.10 及以上版本 / Python 3.10 or newer.
- 可访问的 MySQL 实例（或其他将来扩展的数据源） / Reachable MySQL instance (other engines to be added).

### 安装步骤 | Installation

1. 克隆仓库并进入目录 / Clone the repository and change into the project:
   ```bash
   git clone https://github.com/your-account/mcp-db-python.git
   cd mcp-db-python
   ```
2. （可选）创建虚拟环境并激活 / (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```
3. 安装依赖 / Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. 配置数据库连接 / Configure database credentials:
   - 复制或编辑 `.env` 文件，填写 `DB_TYPE`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME`。  
     Update the `.env` file with the right `DB_TYPE`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, and `DB_NAME` values.

### 启动服务 | Run the Server

使用 Python 启动 MCP 服务（默认通过标准输入/输出通讯） / Launch the MCP server (communicates over stdin/stdout):

```bash
python server.py
```

终端会输出 `MCP Python Server started` 等提示，随后即可通过支持 MCP 的客户端或自定义脚本发送 JSON-RPC 请求。  
The console logs `MCP Python Server started`, after which MCP-aware clients or custom scripts can exchange JSON-RPC messages with the server.

## 可用接口 | Available Tools

| 方法名 / Method | 说明 / Description | 状态 / Status |
| --- | --- | --- |
| `listTables` | 列出当前数据库中的所有表名 / List every table in the configured database. | 已实现 / Completed |
| `getTableSchema` | 返回指定表的字段定义与元数据 / Fetch column metadata for a given table. | 已实现 / Completed |
| `runQuery` | 执行仅限只读的 SQL 查询并返回列与数据行 / Execute read-only SQL and return columns with rows. | 已实现 / Completed |
| `getProcedureDefinition` | 获取指定存储过程的建造语句 / Retrieve the CREATE statement of a stored procedure. | 已实现 / Completed |
| `listDatabases` | 列出当前连接可访问的数据库，方便跨库巡检 / List accessible databases to navigate across schemas. | 已实现 / Completed |
| `listViews` | 查找视图名称并返回定义摘要 / Enumerate views with definition snippets. | 已实现 / Completed |
| `getTableStats` | 汇总表的行数与数据/索引大小等统计信息 / Return row counts and size statistics for tables. | 已实现 / Completed |
| `getIndexInfo` | 查看表上索引的列、类型与唯一性 / Inspect indexes for columns, kinds, and uniqueness. | 已实现 / Completed |
| `findForeignKeys` | 列出外键及其关联关系 / List foreign-key constraints and relationships. | 未开发 / Planned |
| `getTriggers` | 返回触发器列表与定义 / Fetch trigger listings and definitions. | 未开发 / Planned |
| `sampleRows` | 抽样返回指定表的若干数据行 / Sample a handful of rows from a table. | 未开发 / Planned |
| `searchColumns` | 关键字搜索列名或注释 / Search column names/comments by keyword. | 未开发 / Planned |
| `describeColumn` | 输出字段类型、默认值与约束细节 / Provide type, defaults, and constraint details for a column. | 未开发 / Planned |
| `explainQuery` | 对只读 SQL 执行 EXPLAIN，分析执行计划 / Run EXPLAIN on read-only SQL to inspect plans. | 未开发 / Planned |
| `listProcedures` | 罗列存储过程或函数名称 / List stored procedures and functions. | 未开发 / Planned |
| `listUsers` | 汇总实例中用户与权限信息（需相应权限） / Summarize users and privileges (where permitted). | 未开发 / Planned |
| `getServerStatus` | 返回版本、连接数、支持引擎等服务器状态 / Return server status such as version, connections, engines. | 未开发 / Planned |
| `compareSchemas` | 比较两个数据库或表的结构差异 / Compare schema structures between databases/tables. | 未开发 / Planned |
| `generateDDL` | 输出完整的 CREATE TABLE 语句 / Generate full CREATE TABLE DDL. | 未开发 / Planned |

## 配置说明 | Configuration

- `.env` 文件由 `python-dotenv` 自动加载，未配置的项会使用 `config/settings.py` 中的默认值。  
  The `.env` file is loaded automatically through `python-dotenv`; unset keys fall back to the defaults in `config/settings.py`.
- 目前仅实现 MySQL 连接器，若 `DB_TYPE` 非 `mysql` 将抛出 `NotImplementedError`。  
  MySQL is the only connector implemented today; other `DB_TYPE` values raise `NotImplementedError`.
- 根据部署需求可在未来扩展 `db_connectors/` 下的实现并在工具层注册更多方法。  
  You can extend the `db_connectors/` package and register additional tools as new backends become available.

## 开发计划 | Roadmap

- 扩展更多数据库连接器（PostgreSQL、SQLite 等）。  
  Add new database connectors (PostgreSQL, SQLite, and beyond).
- 丰富结构化工具与诊断接口，例如索引分析、表统计等。  
  Ship more structured utilities such as index analysis or table statistics.
- 提供更完善的示例脚本与自动化测试。  
  Publish richer integration examples and automated tests.

欢迎通过 Issue 或 Pull Request 提出需求；接口会持续完善以覆盖更多数据库运维与数据洞察场景。  
Feedback and contributions are welcome—new endpoints will continue to arrive to cover broader database operations and analytics use cases.

## 赞助支持 | Sponsor

如果本项目对你有帮助，欢迎赞助支持后续维护；You can sponsor continued development if this project proves useful:
- 扫描下方微信/支付宝赞助码，或通过支付宝账号 `191341025@qq.com` 支持我。  
  Scan the QR code below (WeChat/Alipay) or tip via Alipay at `191341025@qq.com`.

![sponsor](https://github.com/user-attachments/assets/a18f6a0e-7d7f-46b9-b5ea-532085182772)

## 联系方式 | Contact

- Email: tiansenxu@gmail.com
- Email: 191341025@qq.com

任何问题、建议或合作意向都可以通过以上邮箱联系，我会尽快回复。  
Feel free to reach out with questions, feature requests, or collaboration proposals at the emails above.

## 贡献指南 | Contributing

欢迎提交 Issue 描述使用中的问题，也欢迎直接发起 Pull Request 贡献代码。当前 `main` 分支已开启保护，仅仓库维护者可以直接推送，请从最新 `main` 创建自己的功能分支后再提交 PR；如果你需要在本仓库启用额外的受保护分支，欢迎发送邮件至上述地址与我联系。  
Please open issues for bugs or ideas, and submit pull requests if you would like to contribute improvements. The `main` branch is protected and only maintainers can push to it; branch off `main`, work on your feature branch, then open a PR. If you require additional protected branches for collaboration, email me at the contacts above.
