"""统一日志：文件 + 可选 stderr，并安装全局未捕获异常兜底。

发布版用 ``--noconsole`` 打包，stdout/stderr 被丢弃（在 PyInstaller
windowed 模式下 ``sys.stderr`` 甚至可能是 None），因此所有诊断信息
必须落盘，否则用户遇到闪退时完全无迹可查。
"""

import datetime
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QObject, Signal

from core.paths import log_dir

_LOG_FORMAT = "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s"
_MAX_BYTES = 2 * 1024 * 1024
_BACKUP_COUNT = 3

_log_file_path = None
_installed = False


def _current_log_file():
    return log_dir() / f"app-{datetime.date.today():%Y%m%d}.log"


def setup_logging(level=logging.INFO):
    """安装文件日志（线程安全、可重复调用）。返回日志文件路径。"""
    global _log_file_path

    root = logging.getLogger()
    if getattr(root, "_yg_configured", False):
        return _log_file_path

    root.setLevel(level)
    formatter = logging.Formatter(_LOG_FORMAT)

    _log_file_path = _current_log_file()
    try:
        file_handler = RotatingFileHandler(
            _log_file_path,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # 磁盘只读/无权限时不能因为日志而让程序起不来
        _log_file_path = None

    # 打包后 sys.stderr 可能是 None（PyInstaller windowed 模式），需先判空
    if sys.stderr is not None:
        try:
            stream_handler = logging.StreamHandler(sys.stderr)
            stream_handler.setFormatter(formatter)
            root.addHandler(stream_handler)
        except (ValueError, OSError):
            pass

    root._yg_configured = True
    logging.getLogger(__name__).info(
        "日志已启动；日志文件=%s；Python=%s", _log_file_path, sys.version.split()[0]
    )
    return _log_file_path


def log_file_path():
    """当前日志文件的路径（可能为 None）。"""
    return _log_file_path


def _thread_exception_hook(args):
    logging.getLogger("unhandled").critical(
        "线程 %s 中未捕获的异常",
        args.thread.name if args.thread else "?",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


# 错误对话框的跨线程投递桥：PySide6 不支持把任意 Python 可调用对象
# 直接交给 QMetaObject.invokeMethod，因此用一个 QObject 信号 +
# QueuedConnection 把弹窗调度回主线程。
_bridge = None


class _ErrorDialogBridge(QObject):
    show_error = Signal(str, str)


def _show_error_dialog(title, message):
    """在 Qt 主线程中弹出错误对话框（由 queued 信号调用）。"""
    try:
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(None, title, message)
    except Exception:  # noqa: BLE001 - 展示环节本身不能再抛异常
        logging.getLogger("unhandled").exception("展示错误对话框失败")


def _get_bridge():
    global _bridge
    if _bridge is None:
        from PySide6.QtCore import Qt

        _bridge = _ErrorDialogBridge()
        # 经一层 lambda 转发：槽在模块属性上运行时查找，便于测试替换
        _bridge.show_error.connect(
            lambda title, message: _show_error_dialog(title, message),
            Qt.QueuedConnection,
        )
    return _bridge


def unregister_bridge():
    """释放错误对话框桥（测试与退出流程使用）。"""
    global _bridge
    _bridge = None


def _on_uncaught_exception(exc_type, exc_value, exc_tb):
    logging.getLogger("unhandled").critical(
        "未捕获的异常", exc_info=(exc_type, exc_value, exc_tb)
    )
    try:
        from PySide6.QtWidgets import QApplication

        if QApplication.instance() is None:
            return

        path = log_file_path() or "（日志文件不可用）"
        message = (
            f"发生未预期的错误，程序可能无法继续正常工作。\n\n"
            f"{exc_type.__name__}: {exc_value}\n\n"
            f"详细信息已记录到日志：\n{path}"
        )
        # 从异常上下文直接弹模态框不安全，交给事件循环异步执行
        _get_bridge().show_error.emit("程序错误", message)
    except Exception:  # noqa: BLE001 - 兜底路径本身绝不能再抛异常
        logging.getLogger("unhandled").exception("安排错误对话框失败")


def install_excepthook():
    """安装全局异常兜底（主线程 + 子线程），可重复调用。"""
    global _installed
    if _installed:
        return
    _installed = True
    sys.excepthook = _on_uncaught_exception
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_exception_hook
