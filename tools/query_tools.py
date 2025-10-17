# runQuery、getProcedureDefinition
# tools/query_tools.py
from tools.schema_tools import get_connector


def run_query(sql: str, params=None) -> dict:
    """Execute a read-only SQL query."""
    connector = get_connector()
    return connector.run_query(sql, params=params)


def get_procedure_definition(name: str) -> dict:
    """Fetch stored procedure definition."""
    connector = get_connector()
    return connector.get_procedure_definition(name)


def sample_rows(table_name: str, limit: int = 5) -> dict:
    """抽样返回指定数据表的若干行数据。"""
    connector = get_connector()
    return connector.sample_rows(table_name, limit=limit)


def explain_query(sql: str, params=None) -> list:
    """对只读 SQL 执行 EXPLAIN，返回执行计划。"""
    connector = get_connector()
    return connector.explain_query(sql, params=params)
