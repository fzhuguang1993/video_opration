import pymysql
import hashlib
from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt

DB_CFG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "你的MySQL密码",
    "database": "video_trace_db",
    "charset": "utf8mb4"
}

def md5_encrypt(s: str):
    return hashlib.md5(s.encode("utf-8")).hexdigest()

class ChangePwdDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改密码")
        self.setFixedSize(300, 220)
        self.setup_ui()

    def setup_ui(self):
        lay = QVBoxLayout()
        lay.setSpacing(10)
        lay.setContentsMargins(25,25,25,25)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("用户名:"))
        self.edt_name = QLineEdit()
        h1.addWidget(self.edt_name)
        lay.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("原密码:"))
        self.edt_old = QLineEdit()
        self.edt_old.setEchoMode(QLineEdit.Password)
        h2.addWidget(self.edt_old)
        lay.addLayout(h2)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("新密码:"))
        self.edt_new1 = QLineEdit()
        self.edt_new1.setEchoMode(QLineEdit.Password)
        h3.addWidget(self.edt_new1)
        lay.addLayout(h3)

        h4 = QHBoxLayout()
        h4.addWidget(QLabel("确认新密码:"))
        self.edt_new2 = QLineEdit()
        self.edt_new2.setEchoMode(QLineEdit.Password)
        h4.addWidget(self.edt_new2)
        lay.addLayout(h4)

        btn_lay = QHBoxLayout()
        self.btn_ok = QPushButton("确认修改")
        self.btn_ok.clicked.connect(self.submit_change)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_lay.addWidget(self.btn_ok)
        btn_lay.addWidget(self.btn_cancel)
        lay.addLayout(btn_lay)

        self.setLayout(lay)

    def submit_change(self):
        uname = self.edt_name.text().strip()
        old_pwd = self.edt_old.text().strip()
        new1 = self.edt_new1.text().strip()
        new2 = self.edt_new2.text().strip()

        if not all([uname, old_pwd, new1, new2]):
            QMessageBox.warning(self, "提示", "所有项不能为空")
            return
        if new1 != new2:
            QMessageBox.warning(self, "提示", "两次新密码输入不一致")
            return
        if len(new1) < 4:
            QMessageBox.warning(self, "提示", "新密码至少4位")
            return

        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("SELECT password FROM sys_user WHERE username=%s", (uname,))
            row = cur.fetchone()
            if not row:
                QMessageBox.warning(self, "错误", "该用户名不存在")
                cur.close()
                conn.close()
                return

            db_pwd = row[0]
            old_md5 = md5_encrypt(old_pwd)
            if db_pwd not in (old_pwd, old_md5):
                QMessageBox.warning(self, "错误", "原密码错误")
                cur.close()
                conn.close()
                return

            new_md5 = md5_encrypt(new1)
            cur.execute(
                "UPDATE sys_user SET password=%s WHERE username=%s",
                (new_md5, uname)
            )
            conn.commit()
            cur.close()
            conn.close()
            QMessageBox.information(self, "成功", "密码修改完成，请重新登录")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "异常", str(e))