import pymysql
import hashlib
from PySide6.QtWidgets import (
    QDialog, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt

# ========= 数据库配置（和init_db_and_data保持一致）=========
DB_CFG = {
    "host": "rm-cn-5yd3eq34z000d37o.rwlb.rds.aliyuncs.com",
    "port": 3306,
    "user": "yunying",
    "password": "JvX0Z&kHHNk#6^0b(Up%",
    "database": "yunying_center",
    "charset": "utf8mb4"
}

def md5_encrypt(s: str) -> str:
    """密码MD5加密"""
    return hashlib.md5(s.encode("utf-8")).hexdigest()

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统登录")
        self.setFixedSize(320, 200)
        self.setModal(True)
        # 登录成功后存储用户信息
        self.login_user_info = None
        self.setup_ui()
        #调试锚点开始
        test_btn = QPushButton("测试样式按钮")
        test_btn.setObjectName("primary_btn")
        self.layout().addWidget(test_btn)
        # 调试锚点结束
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(30,30,30,30)

        # 账号行
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("账号："))
        self.edt_user = QLineEdit()
        self.edt_user.setPlaceholderText("输入用户名")
        h1.addWidget(self.edt_user)
        layout.addLayout(h1)

        # 密码行
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("密码："))
        self.edt_pwd = QLineEdit()
        self.edt_pwd.setPlaceholderText("输入密码")
        self.edt_pwd.setEchoMode(QLineEdit.Password)
        h2.addWidget(self.edt_pwd)
        layout.addLayout(h2)

        # 按钮行
        h_btn = QHBoxLayout()
        self.btn_login = QPushButton("登录")
        self.btn_login.clicked.connect(self.do_login)
        self.btn_change_pwd = QPushButton("修改密码")
        self.btn_change_pwd.clicked.connect(self.open_change_pwd)
        h_btn.addWidget(self.btn_login)
        h_btn.addWidget(self.btn_change_pwd)
        layout.addLayout(h_btn)

        self.setLayout(layout)

    def open_change_pwd(self):
        from auth.change_pwd_dialog import ChangePwdDialog
        dlg = ChangePwdDialog(self)
        dlg.exec()

    def do_login(self):
        username = self.edt_user.text().strip()
        pwd = self.edt_pwd.text().strip()
        if not username or not pwd:
            QMessageBox.warning(self, "提示", "账号和密码不能为空！")
            return

        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()
            sql = """
                SELECT id, username, real_name, role, password
                FROM sys_user WHERE username=%s
            """
            cur.execute(sql, (username,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                QMessageBox.warning(self, "错误", "账号不存在")
                return
            uid, uname, realname, role, db_pwd = row
            # 比对MD5密码（后续统一加密存储，当前明文也兼容判断）
            input_md5 = md5_encrypt(pwd)
            if db_pwd not in (pwd, input_md5):
                QMessageBox.warning(self, "错误", "密码不正确")
                return

            # 登录成功，保存用户全局信息
            self.login_user_info = {
                "user_id": uid,
                "username": uname,
                "real_name": realname,
                "role": role
            }
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "数据库异常", f"连接失败：{str(e)}")