# utils/tools/rename/history_manager.py
"""重命名历史记录管理 - 本地JSON存储"""

import os
import json
import uuid
import platform
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from PySide6.QtCore import QThread, Signal


def get_history_dir() -> str:
    """获取历史记录存储目录"""
    system = platform.system()
    if system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~/.config")

    history_dir = os.path.join(base, "movie_operation", "rename_history")
    os.makedirs(history_dir, exist_ok=True)

    # 创建日志目录
    log_dir = os.path.join(history_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    return history_dir


def get_index_path() -> str:
    return os.path.join(get_history_dir(), "index.json")


def get_log_path() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(get_history_dir(), "logs", f"{today}.log")


def generate_batch_id() -> str:
    return str(uuid.uuid4())


def timestamp_to_str(dt: datetime = None) -> str:
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def timestamp_to_filename(dt: datetime = None) -> str:
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d_%H-%M-%S")


def load_index() -> Dict:
    """加载索引文件"""
    index_path = get_index_path()
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"batches": [], "file_index": {}}


def save_index(index: Dict):
    """保存索引文件"""
    index_path = get_index_path()
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def load_batch(batch_id: str) -> Optional[Dict]:
    """加载单个批次数据"""
    history_dir = get_history_dir()
    # 查找对应的文件
    for filename in os.listdir(history_dir):
        if filename.endswith(".json") and filename != "index.json":
            filepath = os.path.join(history_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get("batch_id") == batch_id:
                        return data
            except:
                continue
    return None


def delete_batch_file(batch_id: str) -> bool:
    """删除批次文件"""
    history_dir = get_history_dir()
    for filename in os.listdir(history_dir):
        if filename.endswith(".json") and filename != "index.json":
            filepath = os.path.join(history_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get("batch_id") == batch_id:
                        os.remove(filepath)
                        return True
            except:
                continue
    return False


def write_audit_log(message: str):
    """写入审计日志"""
    log_path = get_log_path()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")


class HistoryManager:
    """历史记录管理器"""

    MAX_RECORDS = 100000  # 最多10万条
    MAX_DAYS = 365  # 保留365天

    def __init__(self):
        self.history_dir = get_history_dir()
        self.index = load_index()
        self._ensure_index_structure()

    def _ensure_index_structure(self):
        """确保索引结构完整"""
        if "batches" not in self.index:
            self.index["batches"] = []
        if "file_index" not in self.index:
            self.index["file_index"] = {}

    def save_batch(self, batch_data: Dict) -> str:
        """保存一批操作记录"""
        batch_id = batch_data.get("batch_id", generate_batch_id())
        batch_data["batch_id"] = batch_id

        if "timestamp" not in batch_data:
            batch_data["timestamp"] = timestamp_to_str()

        # 生成文件名
        dt = datetime.now()
        filename = f"{timestamp_to_filename(dt)}_{batch_id[:8]}.json"
        filepath = os.path.join(self.history_dir, filename)

        # 保存数据
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)

        # 更新索引
        batch_entry = {
            "id": batch_id,
            "timestamp": batch_data["timestamp"],
            "file_count": len(batch_data.get("files", [])),
            "file": filename,
            "user": batch_data.get("user", ""),
            "total": batch_data.get("total", 0),
            "success": batch_data.get("success", 0),
            "failed": batch_data.get("failed", 0)
        }
        self.index["batches"].insert(0, batch_entry)

        # 更新文件索引
        for file_info in batch_data.get("files", []):
            old_path = file_info.get("old_path", "")
            if old_path:
                if old_path not in self.index["file_index"]:
                    self.index["file_index"][old_path] = []
                self.index["file_index"][old_path].append(batch_id)

        # 清理旧数据
        self._cleanup()

        # 保存索引
        save_index(self.index)

        # 写审计日志
        audit_msg = f"[USER:{batch_data.get('user', '未知')}] [BATCH:{batch_id}] 重命名 {batch_data.get('total', 0)} 个文件 成功:{batch_data.get('success', 0)} 失败:{batch_data.get('failed', 0)}"
        write_audit_log(audit_msg)

        return batch_id

    def get_recent_batches(self, limit: int = 50) -> List[Dict]:
        """获取最近的批次列表"""
        return self.index.get("batches", [])[:limit]

    def get_batch_detail(self, batch_id: str) -> Optional[Dict]:
        """获取批次详情"""
        return load_batch(batch_id)

    def get_batches_by_time_range(self, start: str, end: str) -> List[Dict]:
        """按时间范围查询"""
        result = []
        for batch in self.index.get("batches", []):
            if start <= batch["timestamp"] <= end:
                result.append(batch)
        return result

    def get_batches_by_file(self, file_path: str) -> List[Dict]:
        """按文件路径查询历史"""
        batch_ids = self.index.get("file_index", {}).get(file_path, [])
        result = []
        for batch_id in batch_ids:
            batch = load_batch(batch_id)
            if batch:
                result.append(batch)
        return result

    def restore_batch(self, batch_id: str) -> Dict:
        """回退一批操作（返回结果统计）"""
        batch = load_batch(batch_id)
        if not batch:
            return {"success": False, "message": "批次不存在", "restored": 0, "failed": 0}

        restored = 0
        failed = 0
        failed_files = []

        for file_info in batch.get("files", []):
            old_path = file_info.get("old_path", "")
            new_path = file_info.get("new_path", "")

            if not old_path or not new_path:
                continue

            # 检查新文件是否存在
            if os.path.exists(new_path):
                # 检查旧路径是否已被占用
                if os.path.exists(old_path):
                    # 旧路径被占用，重命名冲突
                    failed += 1
                    failed_files.append({"old": old_path, "new": new_path, "reason": "目标路径已存在"})
                    continue

                try:
                    os.rename(new_path, old_path)
                    restored += 1
                except Exception as e:
                    failed += 1
                    failed_files.append({"old": old_path, "new": new_path, "reason": str(e)})
            else:
                # 新文件不存在，可能已被手动删除或移动
                failed += 1
                failed_files.append({"old": old_path, "new": new_path, "reason": "文件不存在"})

        # 写审计日志
        audit_msg = f"[USER:{batch.get('user', '未知')}] [BATCH:{batch_id}] 回退 成功:{restored} 失败:{failed}"
        write_audit_log(audit_msg)

        return {
            "success": True,
            "restored": restored,
            "failed": failed,
            "failed_files": failed_files,
            "total": len(batch.get("files", []))
        }

    def remove_batch(self, batch_id: str) -> bool:
        """删除批次记录（从索引和文件）"""
        # 从索引中移除
        self.index["batches"] = [b for b in self.index["batches"] if b["id"] != batch_id]

        # 从文件索引中移除
        for path, ids in self.index["file_index"].items():
            if batch_id in ids:
                ids.remove(batch_id)
                if not ids:
                    del self.index["file_index"][path]

        # 删除文件
        success = delete_batch_file(batch_id)
        save_index(self.index)
        return success

    def _cleanup(self):
        """清理超出限制的历史记录"""
        batches = self.index.get("batches", [])
        if not batches:
            return

        # 按时间排序（最新的在前）
        batches.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # 先按时间清理（超过365天的）
        now = datetime.now()
        cutoff = now - timedelta(days=self.MAX_DAYS)
        to_delete = []

        for batch in batches:
            try:
                dt = datetime.strptime(batch["timestamp"], "%Y-%m-%d %H:%M:%S")
                if dt < cutoff:
                    to_delete.append(batch)
            except:
                # 如果时间格式解析失败，保留
                continue

        # 如果数量还超过限制，删除最旧的
        remaining = [b for b in batches if b not in to_delete]
        if len(remaining) > self.MAX_RECORDS:
            extra = len(remaining) - self.MAX_RECORDS
            to_delete.extend(remaining[-extra:])

        # 执行删除
        for batch in to_delete:
            self.remove_batch(batch["id"])

    def get_stats(self) -> Dict:
        """获取统计信息"""
        batches = self.index.get("batches", [])
        total_files = sum(b.get("file_count", 0) for b in batches)
        total_success = sum(b.get("success", 0) for b in batches)
        total_failed = sum(b.get("failed", 0) for b in batches)

        return {
            "total_batches": len(batches),
            "total_files": total_files,
            "total_success": total_success,
            "total_failed": total_failed,
            "storage_path": self.history_dir,
            "index_size": len(batches)
        }


class RestoreWorker(QThread):
    """回退异步工作线程"""
    progress = Signal(int, int)
    batch_progress = Signal(str, int, int)  # batch_id, restored, failed
    finished = Signal(bool, str)

    def __init__(self, batch_ids: List[str]):
        super().__init__()
        self.batch_ids = batch_ids
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        manager = HistoryManager()
        total = len(self.batch_ids)
        total_restored = 0
        total_failed = 0
        results = []

        for idx, batch_id in enumerate(self.batch_ids):
            if not self._is_running:
                break

            result = manager.restore_batch(batch_id)
            results.append({
                "batch_id": batch_id,
                "restored": result.get("restored", 0),
                "failed": result.get("failed", 0)
            })
            total_restored += result.get("restored", 0)
            total_failed += result.get("failed", 0)

            self.batch_progress.emit(batch_id, result.get("restored", 0), result.get("failed", 0))
            self.progress.emit(idx + 1, total)

        msg = f"回退完成！成功恢复 {total_restored} 个文件，失败 {total_failed} 个"
        self.finished.emit(True, msg)