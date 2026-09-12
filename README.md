# YG DATA — 接触角数据处理与表面能计算软件

> 基于 PySide6 的接触角数据自动化处理工具：从仪器报告到表面能结果，一站式完成。

---

## 版本说明

**当前版本：2.1.0**（版本号单点定义在 `core/config.py` 的 `APP_VERSION`，`pyproject.toml` 中的 `version` 需同步）

### v2.1.0 主要更新

**可靠性（本次重点）**

- **计算失败不再静默**：OWRK 方程并非对所有接触角组合都有实数解（实测在「水 20–120° × 二碘甲烷 20–100°」区间内约 12.6% 的组合无解，典型为水接触角 > 96° 且二碘甲烷角 < 40°）。此前这类行会静默留空、只在看不见的控制台打印；现在会明确列出**样品名 + 原因**，并提供可展开的明细
- **导出不再导致闪退**：写入失败（文件正在 Excel 中打开、目录只读、磁盘满、路径过长）统一抛出 `ExportError` 并给出可操作提示；此前会抛出未捕获异常，`--noconsole` 打包后表现为窗口直接消失
- **导出列修正**：表头改为取**所有行键的并集**，不再因为首行缺少某字段而静默丢弃该列
- **全局异常兜底 + 文件日志**：新增 `core/logging_setup.py`，未捕获异常写入 `%LOCALAPPDATA%\YG-DATA\logs\` 并弹窗提示；菜单新增「帮助 → 打开日志文件夹」
- **pywin32 惰性导入**：未安装 pywin32 或本机无 Office 时，首页与导电性计算仍可正常使用，仅在导入 Word 时给出明确提示
- **导入失败明细**：未提取到角度的文件不再被丢弃，弹窗逐条列出「文件名 + 原因」，可一键复制
- **线程生命周期修正**：`is_water` 随信号回传（不再回读可能已销毁的 worker 对象）；关窗时等待后台提取线程结束，避免打断 Word COM
- **修复重新导入导致行重复**（原「手工行」判定把上一次的导入行也算作手工行）

**架构与可维护性**

- **表格改为 `QAbstractTableModel`**：新增 `views/models/sample_table_model.py`，以 `list[dict]` 为唯一数据源，替换原先「`current_rows` + `QStandardItemModel` 双份状态、disconnect/reconnect `itemChanged`」的做法；增删改走标准模型通知，选中状态与滚动位置不再丢失
- **新增「序号」列**：保存来源文件名（去扩展名），是稳定的行标识，用户改「样品」列不再影响删除逻辑（此前按「样品」文本关联原始数据，同名样品会被误删）；该列不导出到 Excel
- **业务逻辑下沉**：`core/surface_energy/processor.py` 统一负责计算与统计，UI 不再重复实现
- **删除死代码**：移除零调用的 `core/file_id.py`，并让 `calculate_surface_energies` 真正被 UI 使用
- **公共组件**：`views/widgets/results_table.py`（可编辑结果表）、`views/exporter.py`（导出流程与异常兜底）、`views/dialogs/compat.py`（可测试的对话框封装）
- **配置收敛**：`core/config.py` 单点定义版本号、组织信息与更新源；`core/paths.py` 统一资源与日志路径
- **手册外置**：使用手册移到 `resources/manual.html`，不再与代码混在一起维护

**更新检查**

- 复用单个 `UpdateChecker` 实例（不再每次检查都新建）、请求增加 12 秒超时、检查中禁用菜单项、`v` 前缀只剥一个；Release 描述里写入 `<!-- force-update -->` 可开启强制更新

**打包与测试**

- 打包配置收敛为唯一的 `YG-DATA.spec`（已纳入 git），`build.bat` 改为调用 spec；删除过时的 `YG_DATA.spec`
- **关闭 UPX 压缩**（`upx=False`），避免 PySide6 可执行文件被国产杀毒软件误报
- 新增 `tests/` 共 98 个用例（`unittest`，无需额外依赖），覆盖 OWRK 数值与失败路径、配对与统计、Excel 导出防护、版本解析、导电性计算、界面模型与主窗口装配
- 新增 `pyproject.toml`（含 pytest 与 ruff 配置）、`requirements-dev.txt`；`requirements.txt` 移除未使用的 `pandas`
- 窗口大小与位置持久化；`关于` 与版本号统一取自 `core/config.py`

### v2.0 主要更新（相对 v1.0）

- **架构升级**：由单一功能升级为多页面框架，新增首页与功能卡片导航
- **新增首页**：启动后展示所有可用功能，可点击卡片进入对应页面
- **菜单重构**：“计算方法”菜单切换功能页，“帮助”菜单新增使用手册与关于 YG-DATA
- **数据提取优化**：优先采用汇总行的“平均角度”，避免误取表头或单次测量值；线程内正确初始化 COM，兼容 Word / WPS
- **配对规则调整**：去掉扩展名后文件名完全一致才视为同一样品
- **表格交互增强**：
  - 单元格点击选中，行号点击选中整行（支持 Ctrl / Shift 多选）
  - 样品、水接触角、二碘甲烷接触角三列可手动编辑，其中两个角度列仅允许输入数字
  - 表格下方居中提供“+”按钮，快速追加空行
  - 右键菜单支持删除单元格/行、在上方或下方插入指定数量行、清空全部数据
  - 删除行按行索引操作，空白行不会被误删
- **导出优化**：保留数值类型，自动过滤全空行
- **新增导电性计算页面**（预留扩展示例）
- **新增使用手册与关于对话框**
- **修复多处隐患**：`.docx` 扩展名处理、导出数值类型、资源路径、表格编辑权限等

### v1.0 初始版本

- 单一功能：接触角数据导入、OWRK 表面能计算、Excel 导出

---

## 一、项目简介

本软件是一款基于 **PySide6** 开发的桌面应用程序，面向接触角实验数据的自动化处理。它支持导入实验仪器导出的 Word (`.doc` / `.docx`) 报告，自动提取接触角平均值，按文件名智能配对样品，并基于 **Owens-Wendt (OWRK)** 模型计算固体表面能，最终将结果导出为 Excel 表格。

软件采用多页面框架，首页展示功能卡片，菜单可切换不同计算功能，便于后续持续扩展新的数据处理模块（如导电性计算等）。

---

## 二、主要功能

### 1. 首页与导航

- 启动后进入首页，以卡片形式列出当前所有可用功能
- 点击卡片或通过菜单“计算方法”切换功能页面
- 菜单“帮助”提供使用手册、检查更新与关于 YG-DATA

### 2. 数据导入与解析

- 支持读取旧版 Word (`.doc`) 格式，通过后台调用 Word 或 WPS 静默提取，无弹窗、无闪烁
- 自动从报告表格中定位“平均角度”或“平均接触角”字段，并优先采用汇总行中的“平均角度”值，避免误取表头或单次测量值
- 采用多线程 (`QThread`) 提取数据，提取过程中显示进度弹窗并禁用按钮，防止界面卡死；线程内正确初始化 COM，兼容 Word / WPS

### 3. 智能数据配对

- 按文件名配对：去掉扩展名后文件名完全一致，视为同一样品，合并为一行
- 文件名不一致则视为不同样品，各自独立成行，保留原始数据
- 计算时仅对同时具备水接触角与二碘甲烷接触角的样品执行 OWRK 计算

### 4. 表面能计算

- 内置 OWRK 计算模型，计算极性分量、色散分量和总表面能
- 表格表头：`序号 | 样品 | 水接触角 | 二碘甲烷接触角 | 极性分量 | 色散分量 | 估值方法 | 表面能`
- 所有单元格居中显示
- **模型适用范围**：OWRK 方程组没有非负保证，当水接触角偏大、二碘甲烷接触角偏小时无实数解（实测常见区间约 12.6% 的组合）。此时该行结果留空，并在计算完成提示中列出**具体样品名与原因**，不会静默失败
- 计算前会清空上一次的结果列，避免修改数据后旧结果残留

### 5. 表格交互

- 单元格点击选中，行号点击选中整行（支持 `Ctrl` / `Shift` 多选）
- 双击单元格可手动编辑：样品列可输入任意文本；水接触角与二碘甲烷接触角列仅允许输入数字（支持科学计数法，非法输入会被拒绝并记入日志）；其余五列由计算生成，不可编辑
- 按 `Delete` 键清空选中单元格内容
- 表格下方居中提供“+”按钮，点击在末尾追加一行空行
- 右键菜单支持：
  - 删除选中单元格内容
  - 删除选中行
  - 在上方 / 下方插入指定数量的行
  - 清空全部数据
- 删除行按行内稳定的「序号」（来源文件名）关联原始数据，修改「样品」列不会导致误删
- 重新导入时会保留用户手工录入、尚未计算的行，且不会产生重复行

### 6. 数据展示与导出

- 支持将当前表格内容一键导出为 Excel (`.xlsx`) 文件，保留数值类型
- 导出时自动过滤全空行，「序号」列不会写入文件
- 表头取所有行键的并集，不会因为首行缺字段而丢列
- 写入失败（文件被 Excel 占用、目录只读、磁盘满等）会给出明确提示，不会导致程序崩溃

### 7. 更新检查

- 启动后 3 秒静默检查 GitHub Releases 是否有新版本
- 有新版本时弹窗显示版本号、更新内容，并提供“前往下载”按钮
- 菜单“帮助 → 检查更新”可手动触发；检查中菜单项会禁用，避免重复请求
- 请求带 12 秒超时，网络不可用时静默失败并写入日志
- 在 Release 描述中写入 `<!-- force-update -->` 可开启强制更新（不显示“稍后再说”）
- 无服务器依赖，通过 GitHub 免费托管

### 8. 导电性计算

- 输入电阻、长度、横截面积，计算电阻率与电导率
- 输入框带数字校验器（支持 `1e-5` 这类科学计数法），非法输入即时拦截
- 结果以表格展示（4 位小数 / 6 位有效数字），导出的 Excel 保存**完整精度**数值
- 界面与导出共用同一套格式化函数，避免“看到的”和“导出的”精度不一致

### 9. 日志与故障排查

- 运行日志写入 `%LOCALAPPDATA%\YG-DATA\logs\app-YYYYMMDD.log`（单文件 2 MB 滚动，保留 3 份）
- 未捕获异常（含子线程）会被记录，并弹窗提示日志位置，不再无声闪退
- 菜单“帮助 → 打开日志文件夹”可直接定位

---

## 三、技术栈

| 类别 | 技术 |
| --- | --- |
| 开发语言 | Python 3.9+ |
| GUI 框架 | PySide6 (Qt for Python) + Qt Designer |
| 文件解析 | win32com（后台调用 Word / WPS 读取 `.doc`，惰性导入） |
| Excel 导出 | openpyxl |
| 网络请求 | PySide6.QtNetwork（更新检查） |
| 日志 | 标准库 logging（RotatingFileHandler） |
| 测试 | unittest（`tests/`，无需额外依赖） |
| 打包工具 | PyInstaller（`YG-DATA.spec`） |

---

## 四、项目结构

```text
YG-DATA/
├── main.py                              # 程序入口（安装日志与异常兜底 → 启动界面）
├── build.bat                            # 一键打包脚本（调用 YG-DATA.spec）
├── YG-DATA.spec                         # PyInstaller 打包配置（唯一来源，已纳入 git）
├── pyproject.toml                       # 项目元数据 + pytest / ruff 配置
├── requirements.txt                     # 运行时依赖
├── requirements-dev.txt                 # 开发/打包依赖
├── ui/
│   ├── main_window.ui                   # Qt Designer 设计文件（主窗口骨架）
│   └── main_window_ui.py                # 由 UI 文件生成的 Python 代码
├── views/                               # 界面层（可依赖 core，反之不行）
│   ├── __init__.py
│   ├── main_window.py                   # 主窗口：页面注册、菜单、首页、帮助、更新检查
│   ├── exporter.py                      # 导出流程（保存对话框 + 异常兜底）
│   ├── models/
│   │   └── sample_table_model.py        # 结果表数据模型（QAbstractTableModel）
│   ├── widgets/
│   │   └── results_table.py             # 可编辑结果表组件（右键菜单/Delete/插入行）
│   ├── dialogs/
│   │   ├── compat.py                    # 对话框封装（无交互环境下退化为空实现）
│   │   └── extraction_failures.py       # 导入失败明细对话框
│   └── pages/
│       ├── __init__.py
│       ├── base_page.py                 # 页面基类
│       ├── home_page.py                 # 首页（功能卡片）
│       ├── surface_energy_page.py       # 表面能计算页面
│       └── conductivity_page.py         # 导电性计算页面
├── core/                                # 业务层（不依赖 Qt 界面）
│   ├── __init__.py
│   ├── config.py                        # 版本号 / 组织信息 / 更新源（单点定义）
│   ├── paths.py                         # 资源路径、用户数据目录、日志目录
│   ├── logging_setup.py                 # 日志与全局异常兜底
│   ├── doc_utils.py                     # Word 文档角度提取（返回成功与失败明细）
│   ├── excel_export.py                  # Excel 导出（列并集 + ExportError 防护）
│   ├── updater.py                       # GitHub Releases 版本检查
│   ├── surface_energy/
│   │   ├── __init__.py
│   │   ├── calculator.py                # OWRK 公式与数学域校验
│   │   └── processor.py                 # 配对 + 批量计算 + 统计
│   └── conductivity/
│       ├── __init__.py
│       └── calculator.py                # 导电性公式与展示常量
├── resources/
│   ├── app_icon.ico                     # 应用图标
│   └── manual.html                      # 使用手册正文（外置，便于维护）
├── tests/                               # 单元测试（98 个用例）
│   ├── __init__.py
│   ├── test_surface_energy_calculator.py
│   ├── test_surface_energy_processor.py
│   ├── test_excel_export.py
│   ├── test_updater.py
│   ├── test_doc_utils.py
│   ├── test_conductivity.py
│   └── test_ui_smoke.py
├── tmp/                                 # 测试临时目录（已忽略）
└── .venv/                               # 虚拟环境
```

---

## 五、安装与运行

### 1. 环境要求

- Windows 10 / 11
- Python 3.9+
- Microsoft Word 或 WPS（仅“读取 `.doc` 报告”这一功能需要；未安装时其它功能仍可使用）

### 2. 安装步骤

```bash
# 创建虚拟环境
python -m venv .venv

# 激活（PowerShell）
.venv\Scripts\Activate.ps1

# 激活（cmd）
.venv\Scripts\activate.bat

# 安装依赖
pip install -r requirements.txt
```

`requirements.txt` 内容：

```
PySide6==6.11.2
pywin32==312
openpyxl>=3.1
```

### 3. 运行软件

```bash
python main.py
```

### 4. 运行测试

测试基于标准库 `unittest`，无需额外安装依赖：

```bash
python -m unittest discover -s tests -t .
```

在无桌面环境（CI / 远程会话）中运行时，设置 `QT_QPA_PLATFORM=offscreen` 即可。

安装 `requirements-dev.txt` 后也可用 pytest 运行：

```bash
pip install -r requirements-dev.txt
pytest
```

---

## 六、使用说明

1. 启动后进入首页，点击“表面能计算”卡片或通过菜单“计算方法”进入
2. 点击“导入水滴角”，选择所有水滴角 `.doc` / `.docx` 文件
3. 点击“导入二碘甲烷接触角”，选择所有二碘甲烷 `.doc` / `.docx` 文件
4. 软件自动按文件名配对并提取角度，表格展示样品与角度；若有文件未提取到角度，会弹出**导入失败明细**
5. 如需手动补充或修正，可直接双击可编辑列输入；点击“+”追加空行；右键可插入或删除行
6. 点击“计算表面能”，按 OWRK 模型计算，结果写入后四列；若有样品无实数解，提示中会列出样品名与原因
7. 点击“导出.xlsx文件”，选择保存路径导出结果
8. 菜单“帮助 → 使用手册”可查看详细图文教程
9. 菜单“帮助 → 检查更新”可手动检查新版本；菜单“帮助 → 打开日志文件夹”可查看运行日志

---

## 七、打包说明（Windows 环境）

### 1. 一键打包（推荐）

项目根目录提供 `build.bat`，双击即可自动完成环境检查、清理、打包与错误捕获。

打包参数**全部集中在 `YG-DATA.spec`**（唯一来源），`build.bat` 只负责调用，避免命令行与 spec 两处配置不一致：

```bat
.venv\Scripts\pyinstaller.exe --noconfirm YG-DATA.spec
```

`YG-DATA.spec` 关键配置：

| 配置 | 作用 |
| --- | --- |
| `datas=[('resources', 'resources')]` | 把 resources 目录（含手册、图标）一起打包 |
| `hiddenimports` 含 `win32com*` / `pythoncom` / `pywintypes` | **必须**：这些模块是惰性导入，静态分析看不到 |
| `hiddenimports` 含 `PySide6.QtNetwork` | 更新检查依赖 |
| `excludes` | 排除 QtWebEngine / Qt3D / QtCharts / QtQuick / QtQml / tkinter 等，压缩体积 |
| `console=False` | 不显示黑色命令行窗口 |
| `upx=False` | **关闭 UPX**：压缩 PySide6 可执行文件容易被国产杀毒软件误报 |
| `icon=['resources/app_icon.ico']` | 设置 exe 图标 |

### 2. 手动打包（等价命令）

若不想用 spec，可用下面的等价命令：

```bash
.venv\Scripts\pyinstaller.exe --noconsole --onefile ^
  --name YG-DATA ^
  --icon "resources\app_icon.ico" ^
  --add-data "resources;resources" ^
  --hidden-import win32com ^
  --hidden-import win32com.client ^
  --hidden-import pythoncom ^
  --hidden-import pywintypes ^
  --hidden-import PySide6.QtNetwork ^
  --collect-submodules win32com ^
  main.py
```

> **注意**：cmd 的续行符是 `^`，PowerShell 的续行符是反引号 `` ` ``，两者不能混用。在 PowerShell 中使用 `^` 会报 `Script file '^' does not exist`。

### 3. 成品位置

- 单文件模式：`dist\YG-DATA.exe`
- 中间文件：`build\`（可随时删除）

### 4. 打包后验证清单

- [ ] 窗口正常打开，有图标
- [ ] 首页卡片正常显示
- [ ] 菜单“计算方法”“帮助”可用
- [ ] 能导入 `.doc` 并提取角度；故意混入一个非法文件，确认弹出「导入失败明细」
- [ ] 能计算表面能；构造一个无解的角度组合，确认提示中列出样品名与原因
- [ ] 能导出 Excel（表头不含「序号」列）
- [ ] 帮助 → 检查更新可用
- [ ] 帮助 → 使用手册可用（内容来自 `resources/manual.html`，确认已一并打包）
- [ ] 帮助 → 打开日志文件夹可用
- [ ] 窗口大小/位置在重启后保持

> **建议**：把 exe 拷到**其他目录**（比如桌面）测试，避免读到源码目录的资源掩盖打包问题。

---

## 八、更新机制

### 1. 工作原理

程序通过 **GitHub Releases API** 检查最新版本，无需自建服务器。

```
启动软件
    ↓
3 秒后 → GET https://api.github.com/repos/{owner}/{repo}/releases/latest
    ↓
解析返回的 tag_name（如 v2.0.0）、assets、body
    ↓
与本地版本号比较
    ↓
有新版本 → 弹窗显示更新说明 + “前往下载”按钮
```

### 2. 配置方法

在 `views/main_window.py` 中修改：

```python
GITHUB_OWNER = "yourname"
GITHUB_REPO = "YG-DATA"
UPDATE_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
```

在 `core/config.py` 中设置当前版本号与更新源（**单点定义**，界面、更新检查、关于对话框都从这里取值）：

```python
APP_VERSION = "2.1.0"
GITHUB_OWNER = "yourname"
GITHUB_REPO = "YG-DATA"
```

> 修改版本号后请同步更新 `pyproject.toml` 中的 `version`。

### 3. 发布新版本流程

1. 修改 `core/config.py` 的 `APP_VERSION`（同步 `pyproject.toml`）
2. 运行 `python -m unittest discover -s tests -t .` 确认测试通过
3. 用 `build.bat` 打包
4. 提交代码到 GitHub（`YG-DATA.spec` 已纳入版本控制）
5. 进入仓库 → Releases → Draft a new release
6. Tag 填 `v2.1.0`，填写更新说明，上传 `YG-DATA.exe`
7. Publish release
8. 用户下次启动即收到更新提示

> 如需强制更新（不显示“稍后再说”），在 Release 描述中加入 `<!-- force-update -->`。

### 4. 核心模块

`core/updater.py` 提供 `UpdateChecker` 类，异步检查更新，不阻塞 UI：

- 信号 `update_available(dict)`：有新版本
- 信号 `up_to_date(str)`：已是最新
- 信号 `check_failed(str)`：检查失败
- 信号 `finished()`：本次检查结束（成功或失败）

单个 `UpdateChecker` 实例在主窗口中复用；检查进行中时菜单项禁用，请求带 12 秒超时。

---

## 九、注意事项

- 程序依赖本机 Office 环境读取 `.doc` 文件；若未安装 pywin32，程序仍可启动，仅在导入 Word 时提示安装
- 建议直接使用 `.doc` 格式，`.docx` 也可被识别
- 配对基于文件名：去掉扩展名后文件名需完全一致
- 手动输入时，样品列可输入任意文本；水接触角与二碘甲烷接触角列仅允许数字
- 「序号」列是内部行标识（来源文件名），不导出到 Excel；修改「样品」列不影响配对与删除
- 删除行按行内「序号」关联原始数据，修改样品名不会误删
- 导出时自动过滤全空行，保留数值类型，表头取所有行键的并集
- 更新检查在无网络或 GitHub 不可达时静默失败（写入日志），不影响正常使用
- 运行日志位于 `%LOCALAPPDATA%\YG-DATA\logs\`，反馈问题请附上当天日志

---

## 十、扩展方式

### 新增计算功能

只需三步：

1. 在 `core/<新功能>/calculator.py` 中编写计算逻辑（纯函数，便于测试）
2. 在 `views/pages/` 下新建页面类，继承 `BaseCalculatorPage`，设置 `PAGE_TITLE` 与 `PAGE_KEY`
3. 在 `views/main_window.py` 的 `_PAGE_REGISTRY` 中注册该类及描述、图标

首页卡片、菜单项、页面切换将自动生成，无需修改 UI 文件。

若新功能需要表格与导出，可直接复用：

- `views/models/sample_table_model.py` —— 可编辑表格数据模型
- `views/widgets/results_table.py` —— 带右键菜单、Delete 清空、插入行的表格组件
- `views/exporter.py` —— 带保存对话框与异常兜底的导出流程

### 发布新版本

1. 更新 `core/config.py` 的 `APP_VERSION`
2. 运行 `build.bat` 打包
3. 在 GitHub 创建对应的 Release 并上传 exe
4. 用户在下次启动时收到更新提示

---

## 十一、常见问题

### 打包时提示 `Script file '^' does not exist`

在 PowerShell 中误用了 cmd 的续行符 `^`。改用单行命令，或使用反引号 `` ` `` 续行。

### 打包后无法读取 `.doc`

确认 `YG-DATA.spec` 的 `hiddenimports` 中保留 `win32com`、`win32com.client`、`pythoncom`、`pywintypes`，以及 `collect_submodules('win32com')`。这些模块是惰性导入，静态分析看不到，遗漏会导致运行时才报错。

### 打包后 exe 闪退

先看日志：`%LOCALAPPDATA%\YG-DATA\logs\`，程序已在启动最早期安装日志与异常兜底。
若日志也没有内容，用 `--console` 代替 `--noconsole` 重新打包，命令行运行即可看到具体错误。

### exe 体积过大

正常现象，PySide6 本身较大。可在 `YG-DATA.spec` 的 `excludes` 中继续排除无用模块（QtWebEngine、Qt3D、QtCharts 等）。

### 某行显示“计算失败 / 无实数解”

该接触角组合超出 OWRK 模型的适用范围（方程无实数解），不是程序错误。常见于水接触角偏大（> 96°）而二碘甲烷接触角偏小（< 40°）。请核对数据，或确认两种角度没有填反。

### 导出时提示“无法写入文件”

目标文件正在 Excel 中打开，请关闭后重试；或换一个没有写入限制的位置（如桌面）。

### 更新检查返回 403 / 404

- 403：缺 User-Agent 或 API 限流。代码已加 User-Agent，正常不会触发
- 404：用户名或仓库名写错，或仓库是 Private

### 更新检查国内访问慢

`core/updater.py` 中已设置 12 秒超时（`REQUEST_TIMEOUT_MS`），失败时静默跳过并写入日志，不影响使用。

---

© 2026 YG Lab · YG DATA