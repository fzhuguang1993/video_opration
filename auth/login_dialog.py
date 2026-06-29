import pymysql
import hashlib
from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox, QFrame
)
from PySide6.QtCore import Qt

from config import DB_CFG


def md5_encrypt(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("login_dialog")
        self.setWindowTitle("系统登录")
        self.setFixedSize(500, 440)
        self.setModal(True)
        self.login_user_info = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("login_header")
        header.setFixedHeight(120)
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(6)

        title = QLabel("运营部数据资产中台")
        title.setObjectName("login_title")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        subtitle = QLabel("请登录您的账号")
        subtitle.setObjectName("login_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header)

        body = QFrame()
        body.setObjectName("login_body")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(48, 32, 48, 36)
        body_layout.setSpacing(18)

        lbl_user = QLabel("账号")
        lbl_user.setObjectName("login_field_label")
        body_layout.addWidget(lbl_user)

        self.edt_user = QLineEdit()
        self.edt_user.setObjectName("login_input")
        self.edt_user.setPlaceholderText("请输入用户名")
        self.edt_user.setFixedHeight(42)
        body_layout.addWidget(self.edt_user)

        lbl_pwd = QLabel("密码")
        lbl_pwd.setObjectName("login_field_label")
        body_layout.addWidget(lbl_pwd)

        self.edt_pwd = QLineEdit()
        self.edt_pwd.setObjectName("login_input")
        self.edt_pwd.setPlaceholderText("请输入密码")
        self.edt_pwd.setEchoMode(QLineEdit.Password)
        self.edt_pwd.setFixedHeight(42)
        body_layout.addWidget(self.edt_pwd)

        self.error_label = QLabel("")
        self.error_label.setObjectName("login_error")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        body_layout.addWidget(self.error_label)

        body_layout.addSpacing(6)

        self.btn_login = QPushButton("登 录")
        self.btn_login.setObjectName("login_btn")
        self.btn_login.setFixedHeight(44)
        self.btn_login.clicked.connect(self.do_login)
        body_layout.addWidget(self.btn_login)

        self.btn_change_pwd = QPushButton("修改密码")
        self.btn_change_pwd.setObjectName("login_link_btn")
        self.btn_change_pwd.setFlat(True)
        self.btn_change_pwd.clicked.connect(self.open_change_pwd)
        body_layout.addWidget(self.btn_change_pwd, 0, Qt.AlignCenter)

        main_layout.addWidget(body, 1)

    def open_change_pwd(self):
        from auth.change_pwd_dialog import ChangePwdDialog
        dlg = ChangePwdDialog(self)
        dlg.exec()

    def do_login(self):
        username = self.edt_user.text().strip()
        pwd = self.edt_pwd.text().strip()
        if not username or not pwd:
            self._show_error("账号和密码不能为空！")
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
                self._show_error("账号不存在")
                return
            uid, uname, realname, role, db_pwd = row
            input_md5 = md5_encrypt(pwd)
            if db_pwd not in (pwd, input_md5):
                self._show_error("密码不正确")
                return

            self.login_user_info = {
                "user_id": uid,
                "username": uname,
                "real_name": realname,
                "role": role
            }
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "数据库异常", f"连接失败：{str(e)}")

    def _show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.show()
