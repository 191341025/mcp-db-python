# 封装 JSON-RPC 协议处理
# mcp_protocol/server_base.py
import sys
import json
from tinyrpc.dispatch import RPCDispatcher
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol

from .tool_registry import register_all_tools

# 创建 JSON-RPC 分发器与协议
dispatcher = RPCDispatcher()
protocol = JSONRPCProtocol()
register_all_tools(dispatcher)

@dispatcher.public
def ping():
    """测试 MCP Server 是否可用"""
    return "pong"

def start_server():
    """启动 MCP 服务器 (基于 stdin/stdout 的 JSON-RPC 通信)"""
    print("[INFO] MCP Python Server started. Waiting for requests...", file=sys.stderr)

    while True:
        raw = sys.stdin.readline()
        if not raw:
            break  # EOF -> 停止服务
        try:
            # 解析 JSON-RPC 请求
            request = protocol.parse_request(raw)
            # 分发处理
            response = dispatcher.dispatch(request)
            if response:
                # serialize() 返回 bytes，需要 decode()
                sys.stdout.write(response.serialize().decode("utf-8") + "\n")
                sys.stdout.flush()
        except Exception as e:
            err = json.dumps({"error": str(e)})
            sys.stdout.write(err + "\n")
            sys.stdout.flush()



