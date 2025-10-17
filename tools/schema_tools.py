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
    """列出数据库中的所有表。"""
    connector = get_connector()
    return connector.list_tables()


def get_table_schema(table_name: str) -> list:
    """获取指定表的字段结构。"""
    connector = get_connector()
    return connector.get_table_schema(table_name)


def list_databases() -> list:
    """列出当前连接可访问的数据库。"""
    connector = get_connector()
    return connector.list_databases()


def list_views(snippet_length: int = 160) -> list:
    """列出视图名称并返回定义摘要，snippet_length 控制截断长度。"""
    connector = get_connector()
    return connector.list_views(snippet_length=snippet_length)


def get_table_stats() -> list:
    """汇总当前数据库下各表的统计信息（行数、数据大小等）。"""
    connector = get_connector()
    return connector.get_table_stats()
