# 管理可暴露的 MCP 工具
# mcp_protocol/tool_registry.py
from typing import Optional

from tinyrpc.dispatch import RPCDispatcher

from tools.schema_tools import (
    compare_schemas,
    describe_column,
    find_foreign_keys,
    generate_ddl,
    get_index_info,
    get_server_status,
    get_table_schema,
    get_table_stats,
    get_triggers,
    list_databases,
    list_procedures,
    list_tables,
    list_users,
    list_views,
    search_columns,
)
from tools.query_tools import explain_query, get_procedure_definition, run_query, sample_rows


def register_schema_tools(dispatcher: RPCDispatcher) -> None:
    dispatcher.add_method(list_databases, name="listDatabases")
    dispatcher.add_method(list_views, name="listViews")
    dispatcher.add_method(list_tables, name="listTables")
    dispatcher.add_method(get_table_schema, name="getTableSchema")
    dispatcher.add_method(get_table_stats, name="getTableStats")
    dispatcher.add_method(get_index_info, name="getIndexInfo")

    def find_foreign_keys_rpc(tableName: Optional[str] = None):
        """RPC 包装：把驼峰参数名转换为内部所需的蛇形命名。"""
        return find_foreign_keys(table_name=tableName)

    dispatcher.add_method(find_foreign_keys_rpc, name="findForeignKeys")
    dispatcher.add_method(get_triggers, name="getTriggers")
    dispatcher.add_method(search_columns, name="searchColumns")

    def describe_column_rpc(tableName: str, columnName: str):
        """RPC 包装：描述指定表字段的元数据。"""
        return describe_column(table_name=tableName, column_name=columnName)

    dispatcher.add_method(describe_column_rpc, name="describeColumn")

    def list_procedures_rpc(includeFunctions: bool = True):
        """RPC 包装：控制是否同时返回函数。"""
        return list_procedures(include_functions=includeFunctions)

    dispatcher.add_method(list_procedures_rpc, name="listProcedures")
    dispatcher.add_method(list_users, name="listUsers")
    dispatcher.add_method(get_server_status, name="getServerStatus")

    def compare_schemas_rpc(
        schemaA: str,
        schemaB: str,
        tableName: Optional[str] = None,
    ):
        """RPC 包装：对比两个库或指定表的结构差异。"""
        return compare_schemas(schema_a=schemaA, schema_b=schemaB, table_name=tableName)

    dispatcher.add_method(compare_schemas_rpc, name="compareSchemas")

    def generate_ddl_rpc(tableName: str):
        """RPC 包装：输出指定表的 CREATE TABLE 语句。"""
        return generate_ddl(table_name=tableName)

    dispatcher.add_method(generate_ddl_rpc, name="generateDDL")


def register_query_tools(dispatcher: RPCDispatcher) -> None:
    def run_query_rpc(sql: str, params=None):
        return run_query(sql, params=params)

    def get_procedure_definition_rpc(procedureName: str):
        return get_procedure_definition(procedureName)

    def sample_rows_rpc(tableName: str, limit: int = 5):
        """RPC 包装：抽样指定表数据行。"""
        return sample_rows(table_name=tableName, limit=limit)

    def explain_query_rpc(sql: str, params=None):
        """RPC 包装：执行 EXPLAIN 并返回计划。"""
        return explain_query(sql, params=params)

    dispatcher.add_method(run_query_rpc, name="runQuery")
    dispatcher.add_method(get_procedure_definition_rpc, name="getProcedureDefinition")
    dispatcher.add_method(sample_rows_rpc, name="sampleRows")
    dispatcher.add_method(explain_query_rpc, name="explainQuery")


def register_all_tools(dispatcher: RPCDispatcher) -> None:
    """Register every available tool against the shared dispatcher."""
    register_schema_tools(dispatcher)
    register_query_tools(dispatcher)
