import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from datetime import datetime

import smbclient
from config import SMB_CONFIG


class SMBUtils:
    """SMB文件传输工具类"""

    def __init__(self):
        self.host = SMB_CONFIG.get("host")
        self.share_name = SMB_CONFIG.get("share_name")
        self.username = SMB_CONFIG.get("username")
        self.password = SMB_CONFIG.get("password")
        self.remote_path = SMB_CONFIG.get("remote_path", "").lstrip('/')
        self.port = SMB_CONFIG.get("port", 445)
        self.is_connected = False

        # 注册 SMB 会话
        try:
            smbclient.register_session(
                self.host,
                username=self.username,
                password=self.password,
                port=self.port
            )
            self.is_connected = True
            print(f"✅ SMB 连接成功: {self.host}/{self.share_name}")
        except Exception as e:
            print(f"❌ SMB 注册连接失败: {e}")
            self.is_connected = False

    def is_available(self) -> bool:
        """检查SMB是否可用"""
        return self.is_connected and all([self.host, self.share_name])

    def get_smb_root(self) -> str:
        """获取SMB根路径"""
        return f"//{self.host}/{self.share_name}"

    def build_smb_path(self, remote_subpath: str = "") -> str:
        """构建SMB完整路径"""
        root = self.get_smb_root()
        # 先拼接 remote_path（溯源视频）
        if self.remote_path:
            path = os.path.join(root, self.remote_path)
        else:
            path = root
        # 再拼接子路径（剪辑/日期/运营）
        if remote_subpath:
            path = os.path.join(path, remote_subpath.lstrip('/'))
        return path

    def ensure_remote_dir(self, remote_path: str):
        """确保远程目录存在"""
        if not self.is_available():
            return

        try:
            # 逐级创建目录
            parts = remote_path.replace(self.get_smb_root(), '').strip('/').split('/')
            current_path = self.get_smb_root()

            for part in parts:
                if part:
                    current_path = os.path.join(current_path, part)
                    try:
                        smbclient.listdir(current_path)
                    except:
                        smbclient.mkdir(current_path)
        except Exception as e:
            print(f"创建远程目录失败: {e}")

    def upload_file(
            self,
            local_path: str,
            remote_subpath: str = "",
            filename: str = None,
            log_callback=None
    ) -> Tuple[bool, str]:
        """上传文件到SMB"""
        if not self.is_available():
            return False, "SMB不可用，请检查配置"

        if not os.path.exists(local_path):
            return False, f"文件不存在: {local_path}"

        try:
            if not filename:
                filename = os.path.basename(local_path)

            remote_dir = self.build_smb_path(remote_subpath)
            self.ensure_remote_dir(remote_dir)

            remote_full_path = os.path.join(remote_dir, filename)

            if log_callback:
                log_callback(f"📤 上传到SMB: {filename}")

            with open(local_path, 'rb') as local_file:
                with smbclient.open_file(remote_full_path, 'wb') as remote_file:
                    remote_file.write(local_file.read())

            if log_callback:
                log_callback(f"✅ 上传成功: {filename}")
            return True, remote_full_path

        except Exception as e:
            error_msg = str(e)
            if log_callback:
                log_callback(f"❌ 上传失败: {error_msg}")
            return False, error_msg

    def upload_files(
            self,
            local_paths: List[str],
            remote_subpath: str = "",
            log_callback=None
    ) -> List[Dict]:
        """批量上传文件"""
        results = []
        total = len(local_paths)

        if not self.is_available():
            error_msg = "SMB不可用，请检查配置"
            for local_path in local_paths:
                results.append({
                    "local": local_path,
                    "remote": None,
                    "success": False,
                    "error": error_msg
                })
            return results

        for idx, local_path in enumerate(local_paths):
            if log_callback:
                log_callback(f"📤 上传进度: {idx + 1}/{total}")

            success, result = self.upload_file(
                local_path,
                remote_subpath=remote_subpath,
                log_callback=log_callback
            )
            results.append({
                "local": local_path,
                "remote": result if success else None,
                "success": success,
                "error": result if not success else None
            })

        if log_callback:
            success_count = sum(1 for r in results if r["success"])
            log_callback(f"📤 上传完成: 成功 {success_count}/{total}")

        return results

    def check_connection(self) -> bool:
        """检查SMB连接"""
        if not self.is_available():
            return False
        try:
            smbclient.listdir(self.get_smb_root())
            return True
        except:
            return False

    def list_remote_files(self, remote_subpath: str = "") -> List[str]:
        """列出远程文件"""
        if not self.is_available():
            return []
        try:
            remote_path = self.build_smb_path(remote_subpath)
            files = smbclient.listdir(remote_path)
            return [f for f in files if not f.startswith('.')]
        except:
            return []