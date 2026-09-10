from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame,
    QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from views.pages.base_page import BaseCalculatorPage


class FunctionCard(QFrame):
    """首页上的一个功能卡片，点击后发出 page_key"""
    clicked = Signal(str)

    def __init__(self, title, description, page_key, icon_text="", parent=None):
        super().__init__(parent)
        self.page_key = page_key
        self.setObjectName("FunctionCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(130)
        self.setMinimumWidth(220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setStyleSheet("""
            QFrame#FunctionCard {
                background-color: #ffffff;
                border: 1px solid #d8e3ec;
                border-radius: 10px;
            }
            QFrame#FunctionCard:hover {
                background-color: #f2f8ff;
                border: 1px solid #4a90e2;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        if icon_text:
            icon_label = QLabel(icon_text)
            f = QFont()
            f.setPointSize(22)
            icon_label.setFont(f)
            icon_label.setStyleSheet("color: #4a90e2; background: transparent;")
            layout.addWidget(icon_label)

        title_label = QLabel(title)
        tf = QFont()
        tf.setPointSize(12)
        tf.setBold(True)
        title_label.setFont(tf)
        title_label.setStyleSheet("color: #203040; background: transparent;")
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6b7c8f; background: transparent;")
        layout.addWidget(desc_label)

        layout.addStretch(1)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(
            event.position().toPoint()
        ):
            self.clicked.emit(self.page_key)
        super().mouseReleaseEvent(event)


class HomePage(BaseCalculatorPage):
    PAGE_TITLE = "首页"
    PAGE_KEY = "home"

    navigate = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(8)

        # ---------- 主标题 ----------
        title = QLabel("YG DATA")
        tf = QFont()
        tf.setPointSize(26)
        tf.setBold(True)
        title.setFont(tf)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #203040;")
        layout.addWidget(title)

        # ---------- 描述文本 ----------
        subtitle = QLabel(
            "数据处理自动化流程 —— 从仪器报告到结果汇总，一站式完成"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        sf = QFont()
        sf.setPointSize(11)
        subtitle.setFont(sf)
        subtitle.setStyleSheet("color: #4a6075;")
        layout.addWidget(subtitle)

        layout.addSpacing(24)

        # ---------- 功能卡片区 ----------
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(16)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.cards_container)

        layout.addStretch(1)

        # ---------- 版本 ----------
        version = QApplication.applicationVersion() or "1.0"
        version_label = QLabel(f"版本 {version}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #a0b0c0; font-size: 9pt;")
        layout.addWidget(version_label)

    # ==================== 由主窗口调用 ====================
    def set_functions(self, functions):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not functions:
            empty = QLabel("暂无可用功能")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #a0b0c0; font-size: 11pt;")
            self.cards_layout.addWidget(empty, 0, 0, 1, 3)
            return

        cols = 3
        for i, fn in enumerate(functions):
            card = FunctionCard(
                title=fn.get("title", ""),
                description=fn.get("description", ""),
                page_key=fn["key"],
                icon_text=fn.get("icon", ""),
            )
            card.clicked.connect(self.navigate.emit)
            self.cards_layout.addWidget(card, i // cols, i % cols)

        for c in range(cols):
            self.cards_layout.setColumnStretch(c, 1)