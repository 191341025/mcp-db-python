# MySQL connector adapter
# db_connectors/mysql_connector.py
import mysql.connector
from mysql.connector import Error
from config.settings import DB_CONFIG


class MySQLConnector:
    def __init__(self):
        self.connection = None

    def connect(self):
        """Open a connection if not already connected."""
        if self.connection and self.connection.is_connected():
            return

        try:
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
        """Make sure a live connection exists before running queries."""
        if not self.connection or not self.connection.is_connected():
            self.connect()

    def list_tables(self):
        """Return all table names."""
        self.ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        finally:
            cursor.close()

    def get_table_schema(self, table_name):
        """Return column metadata for a table."""
        self.ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(f"DESCRIBE `{table_name}`;")
            schema = cursor.fetchall()
            return schema
        finally:
            cursor.close()

    def is_read_only_query(self, sql: str) -> bool:
        """Check if the SQL statement is safe (read-only)."""
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
        """Execute a read-only query and return columns and rows."""
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
        """Return CREATE statement for a stored procedure."""
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
        if self.connection and self.connection.is_connected():
            self.connection.close()
