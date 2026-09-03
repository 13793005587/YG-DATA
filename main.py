import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置全局应用信息（名称和版本）
    app.setApplicationName("YG DATA")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("YourOrganization")  # 可选
    app.setOrganizationDomain("yourdomain.com")  # 可选

    window = MainWindow()
    window.show()
    sys.exit(app.exec())