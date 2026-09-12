"""YG DATA 程序入口。

日志与全局异常兜底必须在创建任何 Qt 对象之前安装：发布版以
``--noconsole`` 打包，stdout/stderr 会被丢弃，只有落盘日志才能
在用户遇到闪退时提供线索。
"""

import sys

from core import config
from core.logging_setup import install_excepthook, setup_logging
from core.paths import resource_path


def main():
    log_path = setup_logging()
    install_excepthook()

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from views.main_window import MainWindow

    app = QApplication(sys.argv)

    # 全局应用信息（版本号统一来自 core.config）
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName(config.ORG_NAME)
    app.setOrganizationDomain(config.ORG_DOMAIN)

    icon_path = resource_path("resources", "app_icon.ico")
    app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    if log_path:
        import logging

        logging.getLogger(__name__).info("界面已启动")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
