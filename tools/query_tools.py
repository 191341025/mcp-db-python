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
