from PySide6.QtWidgets import QWidget


class BaseCalculatorPage(QWidget):
    """所有计算功能页面的基类"""
    PAGE_TITLE = "计算页面"
    PAGE_KEY = "base"

    def __init__(self, parent=None):
        super().__init__(parent)

    def on_activated(self):
        """页面被切到前台时调用"""
        pass

    def on_deactivated(self):
        """页面被切走时调用"""
        pass