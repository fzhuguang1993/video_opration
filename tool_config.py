# tool_config.py
"""工具配置 - 统一管理所有工具"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ToolConfig:
    tool_id: str
    name: str
    icon: str
    desc: str
    view_class: Optional[str] = None  # ✅ 加默认值
    worker_class: Optional[str] = None  # ✅ 加默认值


TOOL_REGISTRY: Dict[str, ToolConfig] = {
    "watermark": ToolConfig(
        tool_id="watermark",
        name="水印工具",
        icon="🎬",
        desc="批量添加视频水印",
        view_class="WatermarkView",
        worker_class="WatermarkWorker"
    ),
    "format": ToolConfig(
        tool_id="format",
        name="视频格式化",
        icon="⚙️",
        desc="批量调整码率、分辨率、帧率",
        view_class="FormatView",
        worker_class="FormatWorker"
    ),
    "trace": ToolConfig(
        tool_id="trace",
        name="视频溯源",
        icon="🔍",
        desc="批量重命名并记录溯源信息",
        view_class="TraceView",
        worker_class="TraceWorker"
    ),
    "batch_paste": ToolConfig(
        tool_id="batch_paste",
        name="批量粘贴",
        icon="📋",
        desc="批量粘贴录入工具",
        view_class="BatchPasteView",
        worker_class=None
    ),
    "rename": ToolConfig(
        tool_id="rename",
        name="批量重命名",
        icon="🏷️",
        desc="批量文件重命名，支持前缀/后缀/自增编号",
        view_class="RenameView",
        worker_class="RenameWorker"
    ),
}

def get_tool(tool_id: str) -> ToolConfig:
    return TOOL_REGISTRY.get(tool_id)

def get_all_tools() -> List[ToolConfig]:
    return list(TOOL_REGISTRY.values())