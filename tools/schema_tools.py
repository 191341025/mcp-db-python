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


def get_index_info(table_name: str) -> list:
    """查看指定数据表的索引详情，包括列、顺序、唯一性等。"""
    connector = get_connector()
    return connector.get_index_info(table_name)


def find_foreign_keys(table_name: Optional[str] = None) -> list:
    """列出数据库中的外键约束，可按表名筛选具体关联。"""
    connector = get_connector()
    return connector.find_foreign_keys(table_name)


def get_triggers(table_name: Optional[str] = None) -> list:
    """返回触发器名称、作用表、触发时机及 SQL 定义，可按表过滤。"""
    connector = get_connector()
    return connector.get_triggers(table_name)


def search_columns(keyword: str) -> list:
    """按关键字模糊搜索列名或注释，便于定位字段。"""
    connector = get_connector()
    return connector.search_columns(keyword)


def describe_column(table_name: str, column_name: str) -> dict:
    """输出某个字段的详细元数据（类型、默认值、约束等）。"""
    connector = get_connector()
    return connector.describe_column(table_name, column_name)


def list_procedures(include_functions: bool = True) -> list:
    """罗列当前库的存储过程及（可选）函数。"""
    connector = get_connector()
    return connector.list_procedures(include_functions=include_functions)


def list_users() -> list:
    """汇总实例用户及账号状态信息（需要足够权限）。"""
    connector = get_connector()
    return connector.list_users()


def get_server_status() -> dict:
    """返回服务器版本、连接数、可用引擎等状态数据。"""
    connector = get_connector()
    return connector.get_server_status()


def compare_schemas(schema_a: str, schema_b: str, table_name: Optional[str] = None) -> dict:
    """比较两个数据库（或指定表）的结构差异。"""
    connector = get_connector()
    return connector.compare_schemas(schema_a, schema_b, table_name=table_name)


def generate_ddl(table_name: str) -> dict:
    """输出指定表的 CREATE TABLE 语句。"""
    connector = get_connector()
    return connector.generate_ddl(table_name)
