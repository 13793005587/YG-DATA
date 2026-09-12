"""路径工具：兼容开发环境与 PyInstaller 打包后的运行环境。"""

import os
import sys
from pathlib import Path


def app_root():
    """应用根目录。打包后为解包目录（sys._MEIPASS），开发环境为项目根。"""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def resource_path(*parts):
    """定位随程序分发的资源（如 resources/app_icon.ico）。"""
    return str(app_root().joinpath(*parts))


def user_data_dir():
    """用户可写目录：%LOCALAPPDATA%\\YG-DATA（兜底为临时目录）。"""
    base = (
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("APPDATA")
        or os.path.expanduser("~")
    )
    try:
        p = Path(base) / "YG-DATA"
        p.mkdir(parents=True, exist_ok=True)
        return p
    except OSError:
        import tempfile

        p = Path(tempfile.gettempdir()) / "YG-DATA"
        p.mkdir(parents=True, exist_ok=True)
        return p


def log_dir():
    p = user_data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p
