import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QMessageBox, QDialog,
    QVBoxLayout, QHBoxLayout, QTextBrowser, QPushButton,
    QApplication
)
from PySide6.QtGui import QIcon, QAction, QActionGroup, QDesktopServices
from PySide6.QtCore import Qt, QTimer, QUrl

from ui.main_window_ui import Ui_MainWindow
from views.pages.home_page import HomePage
from views.pages.surface_energy_page import SurfaceEnergyPage
from views.pages.conductivity_page import ConductivityPage
from core.updater import UpdateChecker


# ==================== 更新源配置 ====================
# 改成你自己的 GitHub 用户名和仓库名
GITHUB_OWNER = "13793005587"
GITHUB_REPO = "YG-DATA"
UPDATE_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"


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


# ==================== 资源路径 ====================
def resource_path(relative_path):
    """兼容开发环境与 PyInstaller 打包后环境"""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


# ==================== 使用手册对话框 ====================
class ManualDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用手册 - YG DATA")
        self.resize(720, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet(
            "QTextBrowser { border: none; padding: 20px 28px; "
            "background: #ffffff; color: #303840; font-size: 10.5pt; }"
        )
        browser.setHtml(self._html())
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
    def _html():
        return """
        <style>
            h1 { color: #203040; font-size: 16pt; margin-bottom: 6px; }
            h2 { color: #2a7; font-size: 13pt; margin-top: 22px;
                 border-bottom: 1px solid #e0e8ef; padding-bottom: 4px; }
            h3 { color: #4a6075; font-size: 11.5pt; margin-top: 16px; }
            p, li { line-height: 170%; }
            code { background: #f2f6fa; padding: 1px 5px; border-radius: 3px;
                   color: #c04030; font-family: Consolas, monospace; }
            .tip { background: #f4fbf6; border-left: 3px solid #2a7;
                   padding: 8px 12px; margin: 10px 0; color: #305040; }
            .warn { background: #fff8f0; border-left: 3px solid #e8a040;
                    padding: 8px 12px; margin: 10px 0; color: #7a5020; }
        </style>

        <h1>YG DATA 使用手册</h1>
        <p style="color:#6b7c8f;">数据处理自动化流程 · 接触角分析与表面能计算</p>

        <h2>一、总体流程</h2>
        <p>本软件把“仪器报告 → 数据提取 → 配对计算 → 结果导出”
        串成一条自动化流程，减少手工抄录与公式计算。</p>
        <ol>
          <li>在首页点击需要使用的功能，或在菜单“计算方法”中切换</li>
          <li>导入仪器导出的 Word 报告</li>
          <li>在表格中核对数据，必要时手动修正或补充</li>
          <li>点击“计算”得到结果</li>
          <li>导出为 Excel 文件</li>
        </ol>

        <h2>二、表面能计算</h2>

        <h3>1. 导入数据</h3>
        <ul>
          <li>点击 <b>导入水滴角</b>，选择所有水滴角 Word 文件</li>
          <li>点击 <b>导入二碘甲烷接触角</b>，选择所有二碘甲烷 Word 文件</li>
        </ul>
        <div class="tip">
          两个导入按钮都支持多选，导入顺序不影响结果。
          软件会自动从报告中提取“平均角度”。
        </div>

        <h3>2. 自动配对规则</h3>
        <p>软件按文件名进行配对：<b>去掉扩展名后文件名一致，视为同一样品</b>。</p>
        <ul>
          <li>水滴角 <code>4.doc</code> 与 二碘甲烷 <code>4.doc</code> → 配成一行</li>
          <li>文件名不同 → 视为不同样品，各自独立成行</li>
        </ul>
        <div class="warn">
          请确保水滴角与二碘甲烷的文件名一致，否则不会被自动合并。
        </div>

        <h3>3. 手动编辑</h3>
        <p>以下三列可以手动输入：</p>
        <ul>
          <li><b>样品</b>：可输入数字、汉字、字母、符号等任意文本</li>
          <li><b>水接触角</b>：只能输入数字</li>
          <li><b>二碘甲烷接触角</b>：只能输入数字</li>
        </ul>
        <p>其余四列（极性分量、色散分量、估值方法、表面能）由计算自动生成，不能手动编辑。</p>

        <h3>4. 表格操作</h3>
        <ul>
          <li>单击单元格：选中该单元格</li>
          <li>单击左侧行号：选中整行；<code>Ctrl</code> 加选、<code>Shift</code> 连续选择</li>
          <li>双击单元格：进入编辑</li>
          <li>按 <code>Delete</code>：清空选中单元格内容</li>
          <li>点击表格下方 <b>+</b> 号：在末尾追加一行空行</li>
          <li>右键菜单：
            <ul>
              <li>删除选中单元格内容</li>
              <li>删除选中行</li>
              <li>在上方 / 下方插入多行（可设置数量）</li>
              <li>清空全部数据</li>
            </ul>
          </li>
        </ul>

        <h3>5. 计算与导出</h3>
        <ul>
          <li>点击 <b>计算表面能</b>：按 OWRK 模型计算，结果写入后四列</li>
          <li>点击 <b>导出.xlsx文件</b>：将当前表格内容导出为 Excel</li>
        </ul>
        <div class="tip">
          如果某行只有一种角度，该行会保留但后四列留空；
          计算完成时会提示成功配对、缺少数据的行数。
        </div>

        <h2>三、导电性计算</h2>
        <ul>
          <li>依次输入 样品名称、电阻 R (Ω)、长度 L (cm)、横截面积 A (cm²)</li>
          <li>点击 <b>计算</b>：结果追加到下方表格</li>
          <li>电阻率 ρ = R·A / L (Ω·cm)，电导率 σ = 1/ρ (S/cm)</li>
          <li>点击 <b>导出.xlsx文件</b>：导出所有已计算记录</li>
        </ul>

        <h2>四、常见问题</h2>

        <h3>导入时提示“未在文件中提取到有效接触角”</h3>
        <ul>
          <li>确认文件是仪器原始导出的 Word 报告</li>
          <li>确认报告里存在“平均角度”或“平均接触角”字段</li>
          <li>本机需安装 Microsoft Word 或 WPS，读取 <code>.doc</code> 依赖 Office</li>
        </ul>

        <h3>计算后两行没有合并</h3>
        <ul>
          <li>检查水滴角与二碘甲烷的文件名是否一致（去扩展名后）</li>
          <li>若使用了后缀（如 <code>-I</code>），请改名后再导入</li>
        </ul>

        <h3>导出后 Excel 里是空行</h3>
        <ul>
          <li>导出时会自动过滤全空行，只有含内容的行才会写入</li>
        </ul>

        <h2>五、环境与打包</h2>
        <ul>
          <li>运行环境：Windows + Python 3.x + PySide6</li>
          <li>读取 .doc 需要本机安装 Microsoft Word 或 WPS</li>
          <li>打包命令示例：<br>
              <code>pyinstaller --noconsole --onefile --name YG-DATA main.py</code></li>
        </ul>

        <p style="margin-top:30px;color:#a0b0c0;text-align:center;">
          © 2026 YourOrganization · YG DATA
        </p>
        """


# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("YG DATA")

        icon_path = resource_path(os.path.join("resources", "app_icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 更新检查器占位
        self.updater = None

        self._setup_pages()
        self._setup_menu()
        self._populate_home()

        # 启动进入首页
        self._activate_page(HomePage.PAGE_KEY)

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

        # 首页
        home_action = QAction(HomePage.PAGE_TITLE, self)
        home_action.setCheckable(True)
        home_action.triggered.connect(
            lambda _checked, k=HomePage.PAGE_KEY: self._activate_page(k)
        )
        self._action_group.addAction(home_action)
        calc_menu.addAction(home_action)
        self._page_actions[HomePage.PAGE_KEY] = home_action

        calc_menu.addSeparator()

        # 各功能页
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

        act_check_update = QAction("检查更新", self)
        act_check_update.triggered.connect(lambda: self._check_update(silent=False))
        help_menu.addAction(act_check_update)

        help_menu.addSeparator()

        act_about = QAction("关于 YG-DATA", self)
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
        version = QApplication.applicationVersion() or "1.0.0"
        self.updater = UpdateChecker(version, UPDATE_API_URL, self)
        self.updater.update_available.connect(self._on_update_available)

        if not silent:
            self.updater.up_to_date.connect(
                lambda v: QMessageBox.information(
                    self, "检查更新", f"当前已是最新版本 {v}。"
                )
            )
            self.updater.check_failed.connect(
                lambda msg: QMessageBox.warning(
                    self, "检查更新", f"检查失败：\n{msg}"
                )
            )

        self.updater.check()

    def _on_update_available(self, info):
        remote = info.get("version", "")
        download_url = info.get("download_url", "")
        changelog = info.get("changelog", "（暂无更新说明）")
        force = bool(info.get("force", False))
        current = QApplication.applicationVersion() or "1.0.0"

        if len(changelog) > 800:
            changelog = changelog[:800] + "…"

        text = (
            f"发现新版本：{remote}\n"
            f"当前版本：{current}\n\n"
            f"更新内容：\n{changelog}"
        )

        box = QMessageBox(self)
        box.setWindowTitle("软件更新")
        box.setIcon(QMessageBox.Information)
        box.setText(text)

        btn_download = box.addButton("前往下载", QMessageBox.AcceptRole)
        if not force:
            box.addButton("稍后再说", QMessageBox.RejectRole)

        box.exec()

        if box.clickedButton() == btn_download and download_url:
            QDesktopServices.openUrl(QUrl(download_url))

    # ==================== 帮助 ====================
    def _show_manual(self):
        dlg = ManualDialog(self)
        dlg.exec()

    def _show_about(self):
        QMessageBox.about(
            self,
            "关于 YG-DATA",
            """
            <h3>YG DATA</h3>
            <p><b>版本 2.0</b></p>
            <p>数据处理自动化流程 —— 从仪器报告到结果汇总。</p>
            <p>支持导入实验仪器导出的 Word 报告，自动提取接触角，
            基于 OWRK 模型计算固体表面能的极性分量、色散分量与总表面能，
            并支持一键导出为 Excel。</p>
            <p style="color:#888;">© 2026 YourOrganization</p>
            """
        )