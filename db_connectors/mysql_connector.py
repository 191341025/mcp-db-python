# MySQL connector adapter
# db_connectors/mysql_connector.py
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
