# 管理可暴露的 MCP 工具
# mcp_protocol/tool_registry.py
from tinyrpc.dispatch import RPCDispatcher

from tools.schema_tools import (
    get_table_schema,
    get_table_stats,
    get_index_info,
    list_databases,
    list_tables,
    list_views,
)
from tools.query_tools import get_procedure_definition, run_query


def register_schema_tools(dispatcher: RPCDispatcher) -> None:
    dispatcher.add_method(list_databases, name="listDatabases")
    dispatcher.add_method(list_views, name="listViews")
    dispatcher.add_method(list_tables, name="listTables")
    dispatcher.add_method(get_table_schema, name="getTableSchema")
    dispatcher.add_method(get_table_stats, name="getTableStats")
    dispatcher.add_method(get_index_info, name="getIndexInfo")


def register_query_tools(dispatcher: RPCDispatcher) -> None:
    def run_query_rpc(sql: str, params=None):
        return run_query(sql, params=params)

    def get_procedure_definition_rpc(procedureName: str):
        return get_procedure_definition(procedureName)

    dispatcher.add_method(run_query_rpc, name="runQuery")
    dispatcher.add_method(get_procedure_definition_rpc, name="getProcedureDefinition")


def register_all_tools(dispatcher: RPCDispatcher) -> None:
    """Register every available tool against the shared dispatcher."""
    register_schema_tools(dispatcher)
    register_query_tools(dispatcher)
