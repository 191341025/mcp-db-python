# MySQL connector adapter
# db_connectors/mysql_connector.py
from typing import Optional

import mysql.connector
from mysql.connector import Error
from config.settings import DB_CONFIG


class MySQLConnector:
    def __init__(self):
        self.connection = None

    def connect(self):
        """
        建立与 MySQL 的连接；如果已有活跃连接则直接返回，避免重复握手。
        """
        if self.connection and self.connection.is_connected():
            return

        try:
            # 使用配置中给定的连接信息初始化驱动连接
            self.connection = mysql.connector.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"],
            )
            if self.connection and self.connection.is_connected():
                print(f"[INFO] Connected to MySQL {DB_CONFIG['database']} successfully.")
        except Error as e:
            print(f"[ERROR] MySQL connection failed: {e}")
            self.connection = None
            raise

    def ensure_connection(self):
        """
        确保当前存在一个有效的数据库连接，若断开则尝试重新连接。
        """
        if not self.connection or not self.connection.is_connected():
            self.connect()

    def list_tables(self):
        """
        返回当前选定数据库下的所有数据表名称列表。
        """
        self.ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        finally:
            cursor.close()

    def list_databases(self):
        """
        列出当前 MySQL 会话用户可访问的所有数据库名称，便于跨库巡检。
        """
        self.ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("SHOW DATABASES;")
            databases = [row[0] for row in cursor.fetchall()]
            return databases
        finally:
            cursor.close()

    def list_views(self, snippet_length: int = 160):
        """
        枚举当前数据库中的视图名称，并截取视图定义的摘要信息。
        """
        self.ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("SHOW FULL TABLES WHERE TABLE_TYPE = 'VIEW';")
            view_names = [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

        views = []
        for view_name in view_names:
            # 针对每个视图查询 CREATE 语句，以获取定义内容
            cursor = self.connection.cursor()
            try:
                cursor.execute(f"SHOW CREATE VIEW `{view_name}`;")
                row = cursor.fetchone()
            finally:
                cursor.close()

            definition = ""
            if row:
                # SHOW CREATE VIEW 默认返回 (View, Create View, character_set_client, collation_connection)
                definition = row[1] if len(row) > 1 else ""

            # 将换行压缩为空格并截断为摘要
            snippet = " ".join(definition.split())
            if snippet_length and len(snippet) > snippet_length:
                ellipsis = "..." if snippet_length > 3 else ""
                trim_length = snippet_length - len(ellipsis)
                snippet = snippet[:trim_length] + ellipsis

            views.append(
                {
                    "name": view_name,
                    "definitionSnippet": snippet,
                }
            )

        return views

    def get_table_schema(self, table_name):
        """
        返回指定数据表的字段元数据（字段名、类型、默认值等）。
        """
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(f"DESCRIBE `{table_name}`;")
            schema = cursor.fetchall()
            return schema
        finally:
            cursor.close()

    def get_table_stats(self):
        """
        汇总当前数据库下每张表的行数、空间占用等统计信息。
        """
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    TABLE_NAME AS table_name,
                    ENGINE AS engine,
                    TABLE_ROWS AS table_rows,
                    DATA_LENGTH AS data_length,
                    INDEX_LENGTH AS index_length,
                    DATA_FREE AS data_free,
                    CREATE_TIME AS create_time,
                    UPDATE_TIME AS update_time
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME;
                """,
                (DB_CONFIG["database"],),
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_index_info(self, table_name: str):
        """
        查询指定表的索引结构，包含索引名、列、类型以及唯一性等信息。
        """
        if not table_name:
            raise ValueError("table_name is required for index inspection.")

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(f"SHOW INDEX FROM `{table_name}`;")
            rows = cursor.fetchall()
        finally:
            cursor.close()

        indexes = []
        for row in rows:
            indexes.append(
                {
                    "indexName": row.get("Key_name"),
                    "columnName": row.get("Column_name"),
                    "seqInIndex": row.get("Seq_in_index"),
                    "isUnique": row.get("Non_unique") == 0,
                    "indexType": row.get("Index_type"),
                    "collation": row.get("Collation"),
                    "cardinality": row.get("Cardinality"),
                    "subPart": row.get("Sub_part"),
                    "packed": row.get("Packed"),
                    "nullAllowed": row.get("Null"),
                    "indexComment": row.get("Comment"),
                }
            )
        return indexes

    def find_foreign_keys(self, table_name: Optional[str] = None):
        """
        列出当前库中外键约束，可按表名筛选以查看具体关联关系。
        """
        if table_name is not None and not table_name.strip():
            raise ValueError("table_name must not be blank when provided.")

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            sql = """
                SELECT
                    kcu.CONSTRAINT_NAME AS constraint_name,
                    kcu.TABLE_NAME AS table_name,
                    kcu.COLUMN_NAME AS column_name,
                    kcu.REFERENCED_TABLE_NAME AS referenced_table,
                    kcu.REFERENCED_COLUMN_NAME AS referenced_column,
                    rc.UPDATE_RULE AS update_rule,
                    rc.DELETE_RULE AS delete_rule
                FROM information_schema.KEY_COLUMN_USAGE AS kcu
                JOIN information_schema.REFERENTIAL_CONSTRAINTS AS rc
                  ON kcu.CONSTRAINT_SCHEMA = rc.CONSTRAINT_SCHEMA
                 AND kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                WHERE kcu.CONSTRAINT_SCHEMA = %s
                  AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """
            params = [DB_CONFIG["database"]]
            if table_name:
                sql += " AND kcu.TABLE_NAME = %s"
                params.append(table_name)
            sql += " ORDER BY kcu.TABLE_NAME, kcu.CONSTRAINT_NAME, kcu.ORDINAL_POSITION"

            cursor.execute(sql, params)
            rows = cursor.fetchall()
        finally:
            cursor.close()

        foreign_keys = []
        for row in rows:
            foreign_keys.append(
                {
                    "constraintName": row.get("constraint_name"),
                    "tableName": row.get("table_name"),
                    "columnName": row.get("column_name"),
                    "referencedTable": row.get("referenced_table"),
                    "referencedColumn": row.get("referenced_column"),
                    "updateRule": row.get("update_rule"),
                    "deleteRule": row.get("delete_rule"),
                }
            )
        return foreign_keys

    def get_triggers(self, table_name: Optional[str] = None):
        """
        返回触发器列表及定义内容，可选按表名过滤。
        """
        if table_name is not None and not table_name.strip():
            raise ValueError("table_name must not be blank when provided.")

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            sql = """
                SELECT
                    TRIGGER_NAME AS trigger_name,
                    EVENT_MANIPULATION AS event_manipulation,
                    EVENT_OBJECT_TABLE AS event_table,
                    ACTION_TIMING AS action_timing,
                    ACTION_STATEMENT AS action_statement,
                    CREATED AS created_at
                FROM information_schema.TRIGGERS
                WHERE TRIGGER_SCHEMA = %s
            """
            params = [DB_CONFIG["database"]]
            if table_name:
                sql += " AND EVENT_OBJECT_TABLE = %s"
                params.append(table_name)
            sql += " ORDER BY EVENT_OBJECT_TABLE, TRIGGER_NAME"

            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    def sample_rows(self, table_name: str, limit: int = 5):
        """
        抽样返回指定表的若干行数据，默认限制 5 行。
        """
        if not table_name or not table_name.strip():
            raise ValueError("table_name is required for sampling rows.")
        if "`" in table_name or ";" in table_name:
            raise ValueError("Invalid characters in table_name.")
        if limit <= 0:
            raise ValueError("limit must be a positive integer.")

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = f"SELECT * FROM `{table_name}` LIMIT %s"
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            return {
                "columns": cursor.column_names,
                "rows": rows,
            }
        finally:
            cursor.close()

    def search_columns(self, keyword: str):
        """
        通过关键字搜索列名或列注释，帮助快速定位字段。
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must not be empty for column search.")

        like_pattern = f"%{keyword.strip()}%"

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    TABLE_NAME AS table_name,
                    COLUMN_NAME AS column_name,
                    COLUMN_TYPE AS column_type,
                    IS_NULLABLE AS is_nullable,
                    COLUMN_DEFAULT AS column_default,
                    COLUMN_COMMENT AS column_comment
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND (COLUMN_NAME LIKE %s OR COLUMN_COMMENT LIKE %s)
                ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                (DB_CONFIG["database"], like_pattern, like_pattern),
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def describe_column(self, table_name: str, column_name: str):
        """
        输出指定字段的类型、默认值与约束等详细信息。
        """
        if not table_name or not table_name.strip():
            raise ValueError("table_name is required for column description.")
        if not column_name or not column_name.strip():
            raise ValueError("column_name is required for column description.")

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    TABLE_NAME AS table_name,
                    COLUMN_NAME AS column_name,
                    COLUMN_TYPE AS column_type,
                    IS_NULLABLE AS is_nullable,
                    COLUMN_DEFAULT AS column_default,
                    COLUMN_KEY AS column_key,
                    EXTRA AS extra,
                    COLUMN_COMMENT AS column_comment,
                    CHARACTER_MAXIMUM_LENGTH AS char_length,
                    NUMERIC_PRECISION AS numeric_precision,
                    NUMERIC_SCALE AS numeric_scale
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                  AND COLUMN_NAME = %s
                """,
                (DB_CONFIG["database"], table_name, column_name),
            )
            return cursor.fetchone() or {}
        finally:
            cursor.close()

    def explain_query(self, sql: str, params=None):
        """
        对只读 SQL 执行 EXPLAIN，返回执行计划信息。
        """
        if not self.is_read_only_query(sql):
            raise ValueError("Only read-only SQL statements can be explained.")

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            explain_sql = f"EXPLAIN {sql}"
            cursor.execute(explain_sql, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()

    def list_procedures(self, include_functions: bool = True):
        """
        罗列当前数据库下的存储过程（以及可选的函数）名称及时间信息。
        """
        self.ensure_connection()
        routine_types = ("PROCEDURE", "FUNCTION") if include_functions else ("PROCEDURE",)
        placeholders = ", ".join(["%s"] * len(routine_types))

        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                f"""
                SELECT
                    ROUTINE_NAME AS routine_name,
                    ROUTINE_TYPE AS routine_type,
                    CREATED AS created_at,
                    LAST_ALTERED AS last_altered
                FROM information_schema.ROUTINES
                WHERE ROUTINE_SCHEMA = %s
                  AND ROUTINE_TYPE IN ({placeholders})
                ORDER BY ROUTINE_TYPE, ROUTINE_NAME
                """,
                (DB_CONFIG["database"], *routine_types),
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def list_users(self):
        """
        汇总实例用户列表及账号状态（需具备 mysql.user 查询权限）。
        """
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    User AS user,
                    Host AS host,
                    IFNULL(plugin, '') AS auth_plugin,
                    IFNULL(account_locked, 'N') AS account_locked,
                    IFNULL(password_expired, 'N') AS password_expired
                FROM mysql.user
                ORDER BY User, Host
                """
            )
            return cursor.fetchall()
        except Error as exc:
            raise PermissionError(
                "Failed to read mysql.user. Ensure the account has sufficient privileges."
            ) from exc
        finally:
            cursor.close()

    def get_server_status(self):
        """
        返回服务器版本、连接数、运行时长以及支持引擎等状态信息。
        """
        self.ensure_connection()

        cursor = self.connection.cursor(dictionary=True)
        status = {}
        try:
            cursor.execute("SELECT VERSION() AS version;")
            row = cursor.fetchone()
            status["version"] = row.get("version") if row else None

            cursor.execute("SHOW STATUS LIKE 'Threads_connected';")
            row = cursor.fetchone()
            status["threadsConnected"] = row.get("Value") if row else None

            cursor.execute("SHOW STATUS LIKE 'Uptime';")
            row = cursor.fetchone()
            status["uptimeSeconds"] = row.get("Value") if row else None
        finally:
            cursor.close()

        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SHOW ENGINES;")
            status["engines"] = cursor.fetchall()
        finally:
            cursor.close()

        return status

    def compare_schemas(
        self, schema_a: str, schema_b: str, table_name: Optional[str] = None
    ):
        """
        比较两个数据库（或指定表）的字段差异，输出在各自独有的表与字段差别。
        """
        if not schema_a or not schema_b:
            raise ValueError("schema_a and schema_b are required for comparison.")
        if table_name is not None and not table_name.strip():
            raise ValueError("table_name must not be blank when provided.")

        self.ensure_connection()

        def load_columns(schema: str) -> dict:
            cursor_local = self.connection.cursor(dictionary=True)
            try:
                cursor_local.execute(
                    """
                    SELECT
                        TABLE_NAME AS table_name,
                        COLUMN_NAME AS column_name,
                        COLUMN_TYPE AS column_type,
                        IS_NULLABLE AS is_nullable,
                        COLUMN_DEFAULT AS column_default,
                        COLUMN_KEY AS column_key,
                        EXTRA AS extra,
                        ORDINAL_POSITION AS ordinal_position
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_NAME, ORDINAL_POSITION
                    """,
                    (schema,),
                )
                rows_local = cursor_local.fetchall()
            finally:
                cursor_local.close()

            tables = {}
            for row_local in rows_local:
                table = row_local["table_name"]
                if table_name and table != table_name:
                    continue
                tables.setdefault(table, {})[row_local["column_name"]] = row_local
            return tables

        columns_a = load_columns(schema_a)
        columns_b = load_columns(schema_b)

        if table_name:
            tables_to_check = {table_name}
        else:
            tables_to_check = set(columns_a.keys()) | set(columns_b.keys())

        only_in_a = sorted(t for t in tables_to_check if t in columns_a and t not in columns_b)
        only_in_b = sorted(t for t in tables_to_check if t in columns_b and t not in columns_a)

        diffs = {}
        for table in sorted(tables_to_check):
            cols_a = columns_a.get(table, {})
            cols_b = columns_b.get(table, {})
            if not cols_a or not cols_b:
                continue

            col_names = set(cols_a.keys()) | set(cols_b.keys())
            table_diff = {
                "onlyInA": sorted(name for name in col_names if name in cols_a and name not in cols_b),
                "onlyInB": sorted(name for name in col_names if name in cols_b and name not in cols_a),
                "mismatchedColumns": [],
            }
            for col in sorted(col_names):
                if col not in cols_a or col not in cols_b:
                    continue
                meta_a = cols_a[col]
                meta_b = cols_b[col]
                comparable_fields = ("column_type", "is_nullable", "column_default", "column_key", "extra")
                deviations = {}
                for field in comparable_fields:
                    val_a = meta_a.get(field)
                    val_b = meta_b.get(field)
                    if val_a != val_b:
                        deviations[field] = {"schemaA": val_a, "schemaB": val_b}
                if deviations:
                    table_diff["mismatchedColumns"].append({"column": col, "differences": deviations})
            if table_diff["onlyInA"] or table_diff["onlyInB"] or table_diff["mismatchedColumns"]:
                diffs[table] = table_diff

        return {
            "schemaA": schema_a,
            "schemaB": schema_b,
            "onlyInA": only_in_a,
            "onlyInB": only_in_b,
            "tableDiffs": diffs,
        }

    def generate_ddl(self, table_name: str):
        """
        返回指定表的 CREATE TABLE 语句，便于备份或迁移。
        """
        if not table_name or not table_name.strip():
            raise ValueError("table_name is required to generate DDL.")
        if "`" in table_name or ";" in table_name:
            raise ValueError("Invalid characters in table_name.")

        self.ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`;")
            row = cursor.fetchone()
            if not row:
                return {}
            return {"table": row[0], "createStatement": row[1]}
        finally:
            cursor.close()

    def is_read_only_query(self, sql: str) -> bool:
        """
        校验 SQL 是否为安全的只读语句，禁止多语句与写操作。
        """
        stripped = sql.strip()
        if not stripped:
            return False

        # Disallow multiple statements separated by semicolons (except trailing).
        if ";" in stripped[:-1]:
            return False

        upper_sql = stripped.lstrip("(").upper()
        allowed_prefixes = ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH")
        for prefix in allowed_prefixes:
            if upper_sql.startswith(prefix):
                if prefix == "WITH":
                    # Ensure the WITH clause eventually selects.
                    return "SELECT" in upper_sql
                return True
        return False

    def run_query(self, sql: str, params=None):
        """
        执行已校验为只读的查询，并返回列名与结果行数据。
        """
        if not self.is_read_only_query(sql):
            raise ValueError("Only read-only SQL statements are allowed.")

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            return {
                "columns": cursor.column_names,
                "rows": cursor.fetchall(),
            }
        finally:
            cursor.close()

    def get_procedure_definition(self, procedure_name: str):
        """
        获取指定存储过程的 CREATE 语句定义，便于分析过程逻辑。
        """
        if not procedure_name or "`" in procedure_name or " " in procedure_name:
            raise ValueError("Invalid procedure name.")

        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(f"SHOW CREATE PROCEDURE `{procedure_name}`;")
            result = cursor.fetchone()
            if not result:
                return {}
            return result
        finally:
            cursor.close()

    def close(self):
        """
        主动关闭数据库连接，释放底层资源句柄。
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
