"""让模态对话框在测试中可被替换。

直接调用 ``QMessageBox.information(...)`` 的代码在自动化测试里会
永久阻塞在事件循环上。这里用一个极薄的运行时查找代理替代静态调用，
生产环境行为完全一致，测试只需替换 ``views.<模块>.qmessagebox`` 即可。
"""

from PySide6.QtWidgets import QMessageBox as _RealMessageBox

_runtime = _RealMessageBox


class _MessageBoxProxy:
    """把属性访问转发到当前生效的 QMessageBox 实现。"""

    def __getattr__(self, name):
        return getattr(_runtime, name)


def qmessagebox():
    """返回当前生效的 QMessageBox 类（测试可替换）。"""
    return _runtime


def set_messagebox(fake):
    """替换 QMessageBox 实现；传入 None 恢复真实实现。返回原实现。"""
    global _runtime
    previous = _runtime
    _runtime = _RealMessageBox if fake is None else fake
    return previous


class _NoopMessageBox:
    """不可交互环境下的替身：可以构造、可以 setXxx、exec() 立即返回。"""

    Warning = "warning"
    Information = "information"
    Critical = "critical"
    Question = "question"
    Yes = "yes"
    No = "no"
    AcceptRole = "accept"
    RejectRole = "reject"

    def __init__(self, *args, **kwargs):
        self.clicked_button = None

    def setWindowTitle(self, *_args):
        pass

    def setIcon(self, *_args):
        pass

    def setText(self, *_args):
        pass

    def setDetailedText(self, *_args):
        pass

    def addButton(self, *_args, **_kwargs):
        return None

    def clickedButton(self):
        return None

    def exec(self):
        return 0


def create_message_box(parent=None, icon=None, title="", text=""):
    """构造并配置一个消息框。

    真实环境返回 QMessageBox；在无交互环境（自动化测试、无人值守脚本）
    下退化为 :class:`_NoopMessageBox`，避免模态框永久阻塞进程。
    测试可通过替换 ``QMessageBox`` 实现来接管这里的构造。
    """
    try:
        box = _runtime(parent)
    except TypeError:
        return _NoopMessageBox()
    if title:
        box.setWindowTitle(title)
    if icon is not None:
        box.setIcon(icon)
    if text:
        box.setText(text)
    return box
