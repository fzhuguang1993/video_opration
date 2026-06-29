# ui/views/__init__.py
"""工具视图注册"""

from .format_view import FormatView
from .batch_paste_view import BatchPasteView
from utils.tools.rename import RenameView
from utils.tools.watermark import WatermarkView
from utils.tools.trace import TraceView

VIEW_MAP = {
    "format": FormatView,
    "trace": TraceView,
    "batch_paste": BatchPasteView,
    "rename": RenameView,
    "watermark": WatermarkView,
}

def get_view_class(tool_id: str):
    return VIEW_MAP.get(tool_id)
