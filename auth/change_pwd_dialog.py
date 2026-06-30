import pymysql
import hashlib
from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Qt

from config import DB_CFG
from core.database import get_connection



def md5_encrypt(s: str):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


class ChangePwdDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("change_pwd_dialog")
        self.setWindowTitle("修改密码")
        self.setFixedSize(420, 460)
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("change_pwd_header")
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(4)

        title = QLabel("修改密码")
        title.setObjectName("change_pwd_title")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        subtitle = QLabel("请填写完整信息以修改密码")
        subtitle.setObjectName("change_pwd_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header)

        body = QFrame()
        body.setObjectName("change_pwd_body")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(40, 24, 40, 32)
        body_layout.setSpacing(14)

        lbl1 = QLabel("用户名")
        lbl1.setObjectName("field_label")
        body_layout.addWidget(lbl1)
        self.edt_name = QLineEdit()
        self.edt_name.setObjectName("field_input")
        self.edt_name.setPlaceholderText("请输入用户名")
        self.edt_name.setFixedHeight(40)
        body_layout.addWidget(self.edt_name)

        lbl2 = QLabel("原密码")
        lbl2.setObjectName("field_label")
        body_layout.addWidget(lbl2)
        self.edt_old = QLineEdit()
        self.edt_old.setObjectName("field_input")
        self.edt_old.setPlaceholderText("请输入原密码")
        self.edt_old.setEchoMode(QLineEdit.Password)
        self.edt_old.setFixedHeight(40)
        body_layout.addWidget(self.edt_old)

        lbl3 = QLabel("新密码")
        lbl3.setObjectName("field_label")
        body_layout.addWidget(lbl3)
        self.edt_new1 = QLineEdit()
        self.edt_new1.setObjectName("field_input")
        self.edt_new1.setPlaceholderText("请输入新密码（至少4位）")
        self.edt_new1.setEchoMode(QLineEdit.Password)
        self.edt_new1.setFixedHeight(40)
        body_layout.addWidget(self.edt_new1)

        lbl4 = QLabel("确认新密码")
        lbl4.setObjectName("field_label")
        body_layout.addWidget(lbl4)
        self.edt_new2 = QLineEdit()
        self.edt_new2.setObjectName("field_input")
        self.edt_new2.setPlaceholderText("请再次输入新密码")
        self.edt_new2.setEchoMode(QLineEdit.Password)
        self.edt_new2.setFixedHeight(40)
        body_layout.addWidget(self.edt_new2)

        body_layout.addSpacing(8)

        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(12)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setObjectName("change_pwd_cancel_btn")
        self.btn_cancel.setFixedHeight(42)
        self.btn_cancel.clicked.connect(self.reject)
        btn_lay.addWidget(self.btn_cancel)

        self.btn_ok = QPushButton("确认修改")
        self.btn_ok.setObjectName("change_pwd_ok_btn")
        self.btn_ok.setFixedHeight(42)
        self.btn_ok.clicked.connect(self.submit_change)
        btn_lay.addWidget(self.btn_ok)

        body_layout.addLayout(btn_lay)
        main_layout.addWidget(body, 1)

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
