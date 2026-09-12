import logging
import os

from PySide6.QtCore import QSettings, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
)

from core import config
from core.logging_setup import log_file_path
from core.paths import resource_path, user_data_dir
from core.updater import UpdateChecker
from ui.main_window_ui import Ui_MainWindow
from views.dialogs.compat import create_message_box, qmessagebox
from views.pages.conductivity_page import ConductivityPage
from views.pages.home_page import HomePage
from views.pages.surface_energy_page import SurfaceEnergyPage

logger = logging.getLogger(__name__)


# ==================== 功能注册表 ====================
# 新增功能只需在这里加一项，首页卡片和菜单都会自动生成
_PAGE_REGISTRY = [
    {
        "cls": SurfaceEnergyPage,
        "icon": "💧",
        "description": "通过水与二碘甲烷接触角，基于 OWRK 模型计算固体表面能的极性分量、色散分量和总表面能。",
    },
    {
        "cls": ConductivityPage,
        "icon": "⚡",
        "description": "输入电阻、长度和横截面积，计算样品的电阻率与电导率。",
    },
]


# ==================== 使用手册对话框 ====================
class ManualDialog(QDialog):
    """手册正文放在 resources/manual.html，避免与代码混在一起维护。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"使用手册 - {config.APP_NAME}")
        self.resize(760, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet(
            "QTextBrowser { border: none; padding: 20px 28px; "
            "background: #ffffff; color: #303840; font-size: 10.5pt; }"
        )
        browser.setHtml(self._load_html())
        layout.addWidget(browser, 1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(16, 8, 16, 12)
        btn_row.addStretch(1)
        close_btn = QPushButton("关闭")
        close_btn.setMinimumWidth(80)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    @staticmethod
    def _load_html():
        path = resource_path("resources", "manual.html")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            logger.error("读取使用手册失败：%s（%s）", path, e)
            return (
                "<h2>使用手册缺失</h2>"
                f"<p>未能读取手册文件：<code>{path}</code></p>"
                f"<p>错误信息：{e}</p>"
                "<p>请重新安装本软件，或参考程序目录下的 README.md。</p>"
            )


# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(config.APP_NAME)

        icon_path = resource_path("resources", "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 更新检查器只创建一次，后续检查复用同一实例
        self.updater = UpdateChecker(
            QApplication.applicationVersion() or config.APP_VERSION,
            config.UPDATE_API_URL,
            self,
        )
        self.updater.update_available.connect(self._on_update_available)
        self.updater.finished.connect(self._on_update_finished)
        self._pending_silent_check = False

        self._setup_pages()
        self._setup_menu()
        self._populate_home()

        # 启动进入首页
        self._activate_page(HomePage.PAGE_KEY)

        self._restore_geometry()

        # 启动后延迟 3 秒静默检查更新
        QTimer.singleShot(3000, lambda: self._check_update(silent=True))

    # ==================== 页面 ====================
    def _setup_pages(self):
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.pages = {}

        # 首页
        self.home_page = HomePage(self)
        self.home_page.navigate.connect(self._activate_page)
        self.stack.addWidget(self.home_page)
        self.pages[HomePage.PAGE_KEY] = self.home_page

        # 功能页
        self._registry_entries = []
        for entry in _PAGE_REGISTRY:
            cls = entry["cls"]
            page = cls(self)
            self.stack.addWidget(page)
            self.pages[cls.PAGE_KEY] = page
            self._registry_entries.append((cls, entry))

    def _populate_home(self):
        """把功能列表交给首页渲染卡片"""
        functions = []
        for cls, entry in self._registry_entries:
            functions.append({
                "key": cls.PAGE_KEY,
                "title": cls.PAGE_TITLE,
                "description": entry.get("description", ""),
                "icon": entry.get("icon", ""),
            })
        self.home_page.set_functions(functions)

    # ==================== 菜单 ====================
    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.clear()

        # ---------- 计算方法 ----------
        calc_menu = menubar.addMenu("计算方法")

        self._action_group = QActionGroup(self)
        self._action_group.setExclusive(True)
        self._page_actions = {}

        home_action = QAction(HomePage.PAGE_TITLE, self)
        home_action.setCheckable(True)
        home_action.triggered.connect(
            lambda _checked, k=HomePage.PAGE_KEY: self._activate_page(k)
        )
        self._action_group.addAction(home_action)
        calc_menu.addAction(home_action)
        self._page_actions[HomePage.PAGE_KEY] = home_action

        calc_menu.addSeparator()

        for cls, _entry in self._registry_entries:
            action = QAction(cls.PAGE_TITLE, self)
            action.setCheckable(True)
            action.triggered.connect(
                lambda _checked, k=cls.PAGE_KEY: self._activate_page(k)
            )
            self._action_group.addAction(action)
            calc_menu.addAction(action)
            self._page_actions[cls.PAGE_KEY] = action

        # ---------- 帮助 ----------
        help_menu = menubar.addMenu("帮助")

        act_manual = QAction("使用手册", self)
        act_manual.triggered.connect(self._show_manual)
        help_menu.addAction(act_manual)

        self.act_check_update = QAction("检查更新", self)
        self.act_check_update.triggered.connect(
            lambda: self._check_update(silent=False)
        )
        help_menu.addAction(self.act_check_update)

        act_logs = QAction("打开日志文件夹", self)
        act_logs.triggered.connect(self._open_log_folder)
        help_menu.addAction(act_logs)

        help_menu.addSeparator()

        act_about = QAction(f"关于 {config.APP_NAME}", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ==================== 切换 ====================
    def _activate_page(self, key):
        if key not in self.pages:
            return

        current = self.stack.currentWidget()
        if current is not None and hasattr(current, "on_deactivated"):
            current.on_deactivated()

        page = self.pages[key]
        self.stack.setCurrentWidget(page)

        if key in self._page_actions:
            self._page_actions[key].setChecked(True)

        if hasattr(page, "on_activated"):
            page.on_activated()

    # ==================== 检查更新 ====================
    def _check_update(self, silent=False):
        if self.updater.in_progress:
            if not silent:
                qmessagebox().information(self, "检查更新", "正在检查更新，请稍候…")
            return

        self._pending_silent_check = silent
        self.act_check_update.setEnabled(False)

        if not silent:
            # 静默检查不打扰用户，但仍会把失败写进日志
            self.updater.up_to_date.connect(self._on_up_to_date)
            self.updater.check_failed.connect(self._on_check_failed)

        self.updater.check()

    def _on_update_finished(self):
        self.act_check_update.setEnabled(True)
        if self._pending_silent_check:
            logger.info("后台静默检查更新已结束")
        self._pending_silent_check = False

    def _on_up_to_date(self, version):
        qmessagebox().information(
            self, "检查更新", f"当前已是最新版本 {version}。"
        )

    def _on_check_failed(self, message):
        qmessagebox().warning(self, "检查更新", f"检查失败：\n{message}")

    def _on_update_available(self, info):
        remote = info.get("version", "")
        download_url = info.get("download_url", "")
        changelog = info.get("changelog", "（暂无更新说明）")
        force = bool(info.get("force", False))
        current = QApplication.applicationVersion() or config.APP_VERSION

        if len(changelog) > 800:
            changelog = changelog[:800] + "…"

        text = (
            f"发现新版本：{remote}\n"
            f"当前版本：{current}\n\n"
            f"更新内容：\n{changelog}"
        )

        box = create_message_box(
            self, icon=qmessagebox().Information, title="软件更新", text=text
        )

        btn_download = box.addButton("前往下载", qmessagebox().AcceptRole)
        if not force:
            box.addButton("稍后再说", qmessagebox().RejectRole)

        box.exec()

        if box.clickedButton() == btn_download and download_url:
            QDesktopServices.openUrl(QUrl(download_url))

    # ==================== 帮助 ====================
    def _show_manual(self):
        ManualDialog(self).exec()

    def _open_log_folder(self):
        path = user_data_dir()
        logger.info("用户打开日志目录：%s（当前日志 %s）", path, log_file_path())
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _show_about(self):
        qmessagebox().about(
            self,
            f"关于 {config.APP_NAME}",
            f"""
            <h3>{config.APP_NAME}</h3>
            <p><b>版本 {config.APP_VERSION}</b></p>
            <p>数据处理自动化流程 —— 从仪器报告到结果汇总。</p>
            <p>支持导入实验仪器导出的 Word 报告，自动提取接触角，
            基于 OWRK 模型计算固体表面能的极性分量、色散分量与总表面能，
            并支持一键导出为 Excel。</p>
            <p style="color:#888;">{config.COPYRIGHT}</p>
            """,
        )

    # ==================== 窗口几何持久化 ====================
    def _settings(self):
        return QSettings(config.ORG_NAME, config.APP_NAME)

    def _restore_geometry(self):
        settings = self._settings()
        geometry = settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        state = settings.value("window/state")
        if state is not None:
            self.restoreState(state)

    def closeEvent(self, event):
        try:
            settings = self._settings()
            settings.setValue("window/geometry", self.saveGeometry())
            settings.setValue("window/state", self.saveState())
        except Exception:  # noqa: BLE001 - 保存失败不应阻止退出
            logger.exception("保存窗口状态失败")

        # 等待后台提取线程结束，避免 Word COM 被中途打断
        page = self.pages.get(SurfaceEnergyPage.PAGE_KEY)
        if page is not None and hasattr(page, "shutdown_worker"):
            page.shutdown_worker()

        logger.info("程序退出")
        super().closeEvent(event)
