"""提取失败明细对话框：让用户知道「哪几个文件没读到、为什么」。"""

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)


class ExtractionFailureDialog(QDialog):
    def __init__(self, failures, parent=None):
        super().__init__(parent)
        self.failures = list(failures or [])

        self.setWindowTitle("导入失败明细")
        self.resize(620, 380)

        layout = QVBoxLayout(self)

        label = QLabel(
            f"以下 {len(self.failures)} 个文件未能提取到接触角，"
            "请据此核对文件内容："
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        self.text = QPlainTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setPlainText(self._as_text())
        layout.addWidget(self.text, 1)

        buttons = QDialogButtonBox(self)

        copy_btn = QPushButton("复制到剪贴板")
        copy_btn.clicked.connect(self._copy)
        buttons.addButton(copy_btn, QDialogButtonBox.ActionRole)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        buttons.addButton(close_btn, QDialogButtonBox.AcceptRole)

        row = QHBoxLayout()
        row.addWidget(buttons)
        layout.addLayout(row)

    def _as_text(self):
        lines = []
        for item in self.failures:
            lines.append(f"· {item.get('filename', '?')}")
            lines.append(f"    原因：{item.get('reason', '未知')}")
        return "\n".join(lines)

    def _copy(self):
        QApplication.clipboard().setText(self._as_text())
