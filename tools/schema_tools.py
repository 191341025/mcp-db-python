# listTables、getTableSchema 等实现
# tools/schema_tools.py
from typing import Optional

from config.settings import DB_CONFIG
from db_connectors.mysql_connector import MySQLConnector

_connector: Optional[MySQLConnector] = None


def get_connector() -> MySQLConnector:
    """Return a singleton connector instance based on DB configuration."""
    global _connector
    if _connector is None:
        db_type = DB_CONFIG["type"].lower()
        if db_type == "mysql":
            _connector = MySQLConnector()
        else:
            raise NotImplementedError(f"Unsupported DB type: {db_type}")
    return _connector


def list_tables() -> list:
    """列出数据库中的所有表"""
    connector = get_connector()
    return connector.list_tables()


def get_table_schema(table_name: str) -> list:
    """获取指定表的字段结构"""
    connector = get_connector()
    return connector.get_table_schema(table_name)
