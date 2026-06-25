#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库表格测试 - 原生数据展示
"""

import sys
import pymysql
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt

from config import DB_CFG


class TableTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 数据库表格测试")
        self.setGeometry(200, 100, 1100, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        # 标题
        title = QLabel("📊 视频溯源数据 - 原生表格")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        # 按钮
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 刷新数据")
        refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(refresh_btn)

        self.count_label = QLabel("数据行数: 0")
        btn_layout.addWidget(self.count_label)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 隐藏行号列
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)

        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d0d0d0;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QHeaderView::section {
                background: #f0f0f0;
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid #d0d0d0;
                font-weight: 600;
            }
        """)
        layout.addWidget(self.table)

        # 加载数据
        self.load_data()

    def _get_chinese_number(self, num: int) -> str:
        """将数字转为汉字"""
        chinese_nums = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

        if num <= 10:
            return chinese_nums[num]
        elif num < 20:
            return "十" + (chinese_nums[num - 10] if num - 10 > 0 else "")
        elif num < 100:
            tens = num // 10
            ones = num % 10
            if ones == 0:
                return chinese_nums[tens] + "十"
            else:
                return chinese_nums[tens] + "十" + chinese_nums[ones]
        else:
            return str(num)  # 超过99就用阿拉伯数字

    def load_data(self):
        try:
            conn = pymysql.connect(**DB_CFG)
            cur = conn.cursor()

            cur.execute("""
                SELECT 
                    vt.id,
                    vt.trace_code,
                    vt.video_path,
                    vt.record_date,
                    editor.real_name AS editor_name,
                    operator.real_name AS operator_name
                FROM video_trace vt
                LEFT JOIN sys_user editor ON vt.user_id = editor.id
                LEFT JOIN sys_user operator ON vt.operator_id = operator.id
                ORDER BY vt.record_date DESC
                LIMIT 50
            """)

            data = cur.fetchall()
            cur.close()
            conn.close()

            # ✅ 表头：编号（汉字）
            headers = ["编号", "溯源码", "视频路径", "入库日期", "剪辑", "运营"]
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)

            # 填充数据
            self.table.setRowCount(len(data))
            for row, record in enumerate(data):
                # ✅ 编号使用汉字：一、二、三、四...
                chinese_num = self._get_chinese_number(row + 1)

                values = [
                    chinese_num,  # 汉字编号
                    record[1] or "-",  # 溯源码
                    record[2] or "-",  # 视频路径
                    str(record[3])[:10] if record[3] else "-",  # 入库日期
                    record[4] or "-",  # 剪辑
                    record[5] or "-",  # 运营
                ]

                for col, val in enumerate(values):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)

            # 设置列宽
            widths = [60, 120, 300, 120, 100, 100]
            for i, w in enumerate(widths):
                self.table.setColumnWidth(i, w)

            self.count_label.setText(f"数据行数: {len(data)}")
            print(f"✅ 加载成功: {len(data)} 条数据")

        except Exception as e:
            print(f"❌ 加载失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"加载数据失败:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TableTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()