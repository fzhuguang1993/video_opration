from .base_tool import BaseTool
from .batch_input_tool import BatchInputTool

# 注册所有工具
ALL_TOOLS = [
    BatchInputTool
]

# ID映射字典
TOOL_MAP = {tool.tool_id: tool for tool in ALL_TOOLS}

# 显式导出外部可导入变量
__all__ = ["BaseTool", "ALL_TOOLS", "TOOL_MAP"]