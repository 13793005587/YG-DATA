import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 全局应用信息
    app.setApplicationName("YG DATA")
    app.setApplicationVersion("2.0")            # ← 版本号，发新版时改这里
    app.setOrganizationName("YourOrganization")
    app.setOrganizationDomain("yourdomain.com")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())