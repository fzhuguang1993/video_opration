# utils/tools/trace/worker.py
"""视频溯源后台线程"""

import os
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QThread, Signal

from config import DB_CFG
import pymysql


class TraceWorker(QThread):
    """溯源格式化后台线程"""

    progress = Signal(int, int, str)
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(
        self,
        video_paths: list,
        operator_id: int,
        operator_name: str,
        upload_to_smb: bool = True,
        auto_subpath: bool = True,
        custom_subpath: str = ""
    ):
        super().__init__()
        self.video_paths = video_paths
        self.operator_id = operator_id
        self.operator_name = operator_name
        self.upload_to_smb = upload_to_smb
        self.auto_subpath = auto_subpath
        self.custom_subpath = custom_subpath
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        from utils.trace_utils import TraceUtils
        from utils.smb_utils import SMBUtils

        total = len(self.video_paths)
        success_count = 0
        fail_count = 0
        smb_success = 0
        smb_fail = 0

        user_info = {
            "user_id": None,
            "real_name": "",
            "role": 3
        }

        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("SELECT real_name FROM sys_user WHERE role = 3 LIMIT 1")
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                user_info["real_name"] = row[0]
        except Exception as e:
            self.log.emit(f"⚠️ 获取剪辑信息失败: {e}")

        trace_utils = TraceUtils(user_info)

        smb = None
        if self.upload_to_smb:
            try:
                smb = SMBUtils()
                if smb.is_available():
                    self.log.emit("✅ SMB 连接成功")
                else:
                    self.log.emit("⚠️ SMB 不可用，将跳过上传")
                    smb = None
            except Exception as e:
                self.log.emit(f"⚠️ SMB 连接失败: {e}，将跳过上传")
                smb = None

        processed_files = []
        trace_records = []
        conn = None

        try:
            conn = pymysql.connect(**DB_CFG)
            conn.begin()

            self.log.emit(f"📦 开始处理，共 {total} 个视频")
            self.log.emit(f"👤 运营: {self.operator_name}")

            trace_codes = trace_utils.get_batch_trace_codes(total, self.operator_name, conn)

            if not trace_codes:
                raise Exception("溯源码池中没有可用的溯源码！")

            if len(trace_codes) < total:
                raise Exception(f"溯源码不足！需要 {total} 个，实际获取 {len(trace_codes)} 个")

            self.log.emit(f"✅ 获取 {len(trace_codes)} 个溯源码")

            editor_name = user_info.get("real_name", "未知")
            editor_initials = trace_utils.get_user_initials(editor_name)
            operator_initials = trace_utils.get_user_initials(self.operator_name)
            date_str = datetime.now().strftime("%Y%m%d")

            for idx, video_path in enumerate(self.video_paths):
                if not self._is_running:
                    self.log.emit("⚠️ 用户取消")
                    break

                trace_code = trace_codes[idx]
                old_name = Path(video_path).name
                ext = Path(video_path).suffix.upper() or ".MP4"

                new_name = f"{trace_code}_{date_str}_{editor_initials}_{operator_initials}{ext}"

                self.progress.emit(idx + 1, total, new_name)
                self.log.emit(f"📝 [{idx + 1}/{total}] {old_name}")
                self.log.emit(f"   └─ → {new_name}")

                try:
                    result = trace_utils.rename_video(video_path, new_name)
                    if result[0]:
                        actual_new_path = result[1]
                        processed_files.append((video_path, actual_new_path))

                        trace_records.append({
                            "trace_code": trace_code,
                            "video_path": actual_new_path,
                            "user_id": user_info.get("user_id")
                        })

                        self.log.emit("   └─ ✅ 重命名成功")

                        if smb:
                            try:
                                if self.auto_subpath:
                                    sub = f"{editor_initials}/{date_str}"
                                elif self.custom_subpath:
                                    sub = self.custom_subpath
                                else:
                                    sub = ""

                                ok, remote = smb.upload_file(
                                    actual_new_path,
                                    remote_subpath=sub,
                                    log_callback=lambda m: self.log.emit(f"   └─ {m}")
                                )
                                if ok:
                                    smb_success += 1
                                else:
                                    smb_fail += 1
                            except Exception as smb_e:
                                self.log.emit(f"   └─ ⚠️ SMB上传失败: {smb_e}")
                                smb_fail += 1

                        success_count += 1
                    else:
                        self.log.emit(f"   └─ ❌ 重命名失败: {result[1]}")
                        fail_count += 1

                except Exception as e:
                    self.log.emit(f"   └─ ❌ 失败: {str(e)}")
                    fail_count += 1

            if trace_records:
                trace_utils.save_trace_records(trace_records, conn)
                self.log.emit(f"💾 {len(trace_records)} 条溯源记录已保存")

            conn.commit()
            self.log.emit("✅ 事务提交成功")

        except Exception as e:
            if conn:
                conn.rollback()
                self.log.emit(f"❌ 事务已回滚: {str(e)}")

            for old_path, new_path in processed_files:
                try:
                    if os.path.exists(new_path):
                        os.rename(new_path, old_path)
                        self.log.emit(f"🔄 已恢复: {Path(old_path).name}")
                except Exception:
                    self.log.emit(f"⚠️ 回滚失败: {Path(old_path).name}")

            fail_count = total - success_count

        finally:
            if conn:
                conn.close()

        msg = f"溯源格式化完成！\n成功: {success_count}，失败: {fail_count}"
        if self.upload_to_smb and smb:
            msg += f"\nSMB上传: 成功 {smb_success}，失败 {smb_fail}"
        self.finished.emit(success_count > 0 or success_count == total, msg)


class BindWorker(QThread):
    """视频绑定后台线程"""
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, parent_trace_code: str, child_trace_codes: list, action: str = "bind", user_id=None):
        super().__init__()
        self.parent_trace_code = parent_trace_code
        self.child_trace_codes = child_trace_codes
        self.action = action
        self.user_id = user_id

    def run(self):
        conn = None
        cur = None
        success_count = 0
        fail_count = 0

        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()

            if self.action == "bind":
                cur.execute("SELECT id FROM video_trace WHERE trace_code = %s", (self.parent_trace_code,))
                if not cur.fetchone():
                    raise Exception(f"母版溯源码 {self.parent_trace_code} 不存在")

                for child_code in self.child_trace_codes:
                    try:
                        cur.execute("SELECT id FROM video_trace WHERE trace_code = %s", (child_code,))
                        if not cur.fetchone():
                            self.log.emit(f"⚠️ 子视频 {child_code} 不存在，跳过")
                            fail_count += 1
                            continue

                        cur.execute("SELECT id FROM video_bind WHERE trace_code = %s", (child_code,))
                        if cur.fetchone():
                            self.log.emit(f"⚠️ {child_code} 已被绑定，跳过")
                            fail_count += 1
                            continue

                        cur.execute("SELECT id FROM video_bind WHERE trace_code = %s", (self.parent_trace_code,))
                        if cur.fetchone():
                            self.log.emit(f"⚠️ {self.parent_trace_code} 本身已被绑定，不能作为母版")
                            fail_count += 1
                            continue

                        cur.execute("""
                            INSERT INTO video_bind (trace_code, bind_trace_code, user_id, bind_time)
                            VALUES (%s, %s, %s, NOW())
                        """, (child_code, self.parent_trace_code, self.user_id))

                        self.log.emit(f"✅ {child_code} → {self.parent_trace_code}")
                        success_count += 1

                    except Exception as e:
                        self.log.emit(f"❌ {child_code} 绑定失败: {str(e)}")
                        fail_count += 1

                conn.commit()

            elif self.action == "unbind":
                for child_code in self.child_trace_codes:
                    try:
                        cur.execute("""
                            DELETE FROM video_bind 
                            WHERE trace_code = %s AND bind_trace_code = %s
                        """, (child_code, self.parent_trace_code))

                        if cur.rowcount > 0:
                            self.log.emit(f"✅ 已解绑: {child_code} ← {self.parent_trace_code}")
                            success_count += 1
                        else:
                            self.log.emit(f"⚠️ 未找到绑定关系: {child_code} → {self.parent_trace_code}")
                            fail_count += 1
                    except Exception as e:
                        self.log.emit(f"❌ 解绑失败 {child_code}: {str(e)}")
                        fail_count += 1

                conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            self.log.emit(f"❌ 操作失败: {str(e)}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        action_name = "绑定" if self.action == "bind" else "解绑"
        msg = f"{action_name}完成！成功: {success_count}，失败: {fail_count}"
        self.finished.emit(success_count > 0, msg)
