#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.config import get_config
from core.logger import setup_logger
from ui.main_window import MainWindow
from auth.login_dialog import LoginDialog


# main.py
def setup_application() -> QApplication:
    """初始化应用程序"""
    app = QApplication(sys.argv)

    config = get_config()
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName("MovieStudio")

    font = QFont("PingFang SC, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial", 9)
    app.setFont(font)

    app.setStyle("Fusion")

    # ✅ 添加这行：应用样式表
    app.setStyleSheet(config.full_stylesheet)

    return app


def show_login_dialog() -> dict:
    """显示登录对话框，返回用户信息"""
    login_dlg = LoginDialog()
    login_result = login_dlg.exec()

    if login_result != LoginDialog.Accepted:
        return None

    if not login_dlg.login_user_info:
        QMessageBox.critical(None, "登录失败", "获取用户信息失败，请重新登录")
        return None

    return login_dlg.login_user_info


def main():
    """主函数"""
    logger = setup_logger("main")
    logger.info("=" * 60)
    logger.info("📊 运营部数据资产中台 启动中...")
    logger.info("=" * 60)

    try:
        app = setup_application()
        config = get_config()

        logger.info(f"应用版本: v{config.APP_VERSION}")

        while True:
            logger.info("显示登录对话框...")
            user_info = show_login_dialog()

            if user_info is None:
                logger.info("用户取消登录或登录失败，程序退出")
                sys.exit(0)

            logger.info(f"用户登录成功: {user_info.get('real_name', '未知')} (ID: {user_info.get('user_id')})")
            logger.info(f"用户角色: {user_info.get('role', '未知')}")

            logger.info("初始化主窗口...")
            window = MainWindow()

            def on_logout():
                logger.info("用户登出，关闭主窗口")
                window._logout_triggered = True
                window.close()

            window.logout_signal.connect(on_logout)

            window.set_current_user(user_info)
            window.show()
            logger.info("主窗口已显示")

            logger.info("进入事件循环...")
            exit_code = app.exec()
            logger.info(f"主窗口事件循环结束，退出码: {exit_code}")

            if not getattr(window, '_logout_triggered', False):
                logger.info("窗口正常关闭，程序退出")
                break

            logger.info("用户登出，重新显示登录对话框...")

        logger.info("应用程序退出")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("用户中断程序")
        sys.exit(0)
    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"程序崩溃:\n{error_msg}")
        try:
            QMessageBox.critical(None, "程序崩溃", f"发生未处理的异常:\n\n{str(e)}")
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()