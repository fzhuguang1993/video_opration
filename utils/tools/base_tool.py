from abc import ABC, abstractmethod

class BaseTool(ABC):
    # 工具唯一标识
    tool_id: str
    # 按钮显示名称
    name: str
    # 图标emoji
    icon: str
    # 工具描述（弹窗里显示）
    desc: str

    @abstractmethod
    def run(self):
        """执行工具主逻辑"""
        pass