"""测试包：共享的 Qt 环境准备。"""

import itertools
import os
import sys
import tempfile
import unittest

# Qt 无界面运行（CI / 无桌面环境）
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 允许从项目根目录直接运行 python -m unittest discover
sys.path.insert(0, PROJECT_ROOT)

# 测试临时目录优先放在项目内（tmp/，已被 .gitignore 忽略），
# 系统临时目录作为兜底。不使用 tempfile.mkdtemp 的随机目录名：
# 部分受限环境（沙箱、只读盘）下这类目录不可写。
_TMP_CANDIDATES = (os.path.join(PROJECT_ROOT, "tmp"), tempfile.gettempdir())

_counter = itertools.count(1)
_writable_root = None


def _test_root():
    """返回第一个可写的测试临时根目录。"""
    global _writable_root
    if _writable_root is not None:
        return _writable_root
    for candidate in _TMP_CANDIDATES:
        try:
            os.makedirs(candidate, exist_ok=True)
            probe = os.path.join(candidate, f".write-probe-{os.getpid()}")
            with open(probe, "w", encoding="utf-8") as handle:
                handle.write("x")
            os.remove(probe)
        except OSError:
            continue
        _writable_root = candidate
        return candidate
    raise RuntimeError("找不到可写的临时目录，测试无法运行")


def make_temp_dir(prefix="test-"):
    """创建一个可写的唯一目录，返回其绝对路径。"""
    root = _test_root()
    while True:
        path = os.path.join(root, f"{prefix}{next(_counter):04d}-{os.getpid()}")
        try:
            os.makedirs(path, exist_ok=False)
        except FileExistsError:
            continue
        return path


_QT_AVAILABLE = None


def qt_available():
    """检测 PySide6 是否可用（缺失时相关用例整体跳过）。"""
    global _QT_AVAILABLE
    if _QT_AVAILABLE is None:
        try:
            import PySide6  # noqa: F401

            _QT_AVAILABLE = True
        except ImportError:
            _QT_AVAILABLE = False
    return _QT_AVAILABLE


requires_qt = unittest.skipUnless(qt_available(), "未安装 PySide6")
