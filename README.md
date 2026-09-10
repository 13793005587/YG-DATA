# YG DATA — 接触角数据处理与表面能计算软件

> 基于 PySide6 的接触角数据自动化处理工具：从仪器报告到表面能结果，一站式完成。

---

## 版本说明

**当前版本：2.0**

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
- 表格表头：`样品 | 水接触角 | 二碘甲烷接触角 | 极性分量 | 色散分量 | 估值方法 | 表面能`
- 所有单元格居中显示

### 5. 表格交互

- 单元格点击选中，行号点击选中整行（支持 `Ctrl` / `Shift` 多选）
- 双击单元格可手动编辑：样品列可输入任意文本；水接触角与二碘甲烷接触角列仅允许输入数字；其余四列由计算生成，不可编辑
- 按 `Delete` 键清空选中单元格内容
- 表格下方居中提供“+”按钮，点击在末尾追加一行空行
- 右键菜单支持：
  - 删除选中单元格内容
  - 删除选中行
  - 在上方 / 下方插入指定数量的行
  - 清空全部数据
- 删除行按行索引操作，空白行不会被误删

### 6. 数据展示与导出

- 支持将当前表格内容一键导出为 Excel (`.xlsx`) 文件，保留数值类型
- 导出时自动过滤全空行

### 7. 更新检查

- 启动后 3 秒静默检查 GitHub Releases 是否有新版本
- 有新版本时弹窗显示版本号、更新内容，并提供“前往下载”按钮
- 菜单“帮助 → 检查更新”可手动触发
- 无服务器依赖，通过 GitHub 免费托管

### 8. 导电性计算（预留功能）

- 输入电阻、长度、横截面积，计算电阻率与电导率
- 结果以表格展示，可导出 Excel
- 该页面为功能扩展示例，后续可替换为实际公式与字段

---

## 三、技术栈

| 类别 | 技术 |
| --- | --- |
| 开发语言 | Python 3.x |
| GUI 框架 | PySide6 (Qt for Python) + Qt Designer |
| 数据处理 | Pandas |
| 文件解析 | win32com（后台调用 Word / WPS 读取 `.doc`） |
| Excel 导出 | openpyxl |
| 网络请求 | PySide6.QtNetwork（更新检查） |
| 打包工具 | PyInstaller |

---

## 四、项目结构

```text
YG-DATA/
├── main.py                          # 程序入口（含版本号定义）
├── build.bat                        # 一键打包脚本
├── requirements.txt                 # 依赖清单
├── ui/
│   ├── main_window.ui               # Qt Designer 设计文件（主窗口骨架）
│   └── main_window_ui.py            # 由 UI 文件生成的 Python 代码
├── views/
│   ├── __init__.py
│   ├── main_window.py               # 主窗口：页面注册、菜单、首页、帮助、更新检查
│   └── pages/
│       ├── __init__.py
│       ├── base_page.py             # 页面基类
│       ├── home_page.py             # 首页（功能卡片）
│       ├── surface_energy_page.py   # 表面能计算页面
│       └── conductivity_page.py     # 导电性计算页面（预留）
├── core/
│   ├── __init__.py
│   ├── doc_utils.py                 # Word 文档角度提取（通用）
│   ├── excel_export.py              # Excel 导出（通用）
│   ├── updater.py                   # GitHub Releases 版本检查
│   ├── file_id.py                   # 文件名核心标识提取（备用）
│   ├── surface_energy/
│   │   ├── __init__.py
│   │   ├── calculator.py            # OWRK 计算公式
│   │   └── processor.py             # 配对 + 批量计算
│   └── conductivity/
│       ├── __init__.py
│       └── calculator.py            # 导电性计算公式（预留）
├── resources/
│   └── app_icon.ico                 # 应用图标
├── data/                            # 存放数据文件（可选）
└── .venv/                           # 虚拟环境
```

---

## 五、安装与运行

### 1. 环境要求

- Windows 10 / 11
- Python 3.9+
- Microsoft Word 或 WPS（用于读取 `.doc` 文件）

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
pandas>=2.2
openpyxl>=3.1
```

### 3. 运行软件

```bash
python main.py
```

---

## 六、使用说明

1. 启动后进入首页，点击“表面能计算”卡片或通过菜单“计算方法”进入
2. 点击“导入水滴角”，选择所有水滴角 `.doc` / `.docx` 文件
3. 点击“导入二碘甲烷接触角”，选择所有二碘甲烷 `.doc` / `.docx` 文件
4. 软件自动按文件名配对并提取角度，表格展示样品与角度
5. 如需手动补充或修正，可直接双击可编辑列输入；点击“+”追加空行；右键可插入或删除行
6. 点击“计算表面能”，按 OWRK 模型计算，结果写入后四列
7. 点击“导出.xlsx文件”，选择保存路径导出结果
8. 菜单“帮助 → 使用手册”可查看详细图文教程
9. 菜单“帮助 → 检查更新”可手动检查新版本

---

## 七、打包说明（Windows 环境）

### 1. 一键打包（推荐）

项目根目录提供 `build.bat`，双击即可自动完成清理、打包、错误捕获。脚本内容：

```bat
@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================
echo   开始打包 YG-DATA
echo ====================================

echo [1/3] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] 开始打包...
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
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.QtCharts ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtQml ^
  --exclude-module matplotlib ^
  --exclude-module numpy ^
  main.py

if errorlevel 1 (
    echo.
    echo ====================================
    echo   打包失败！
    echo ====================================
    pause
    exit /b 1
)

echo [3/3] 完成！
echo.
echo 成品位置：dist\YG-DATA.exe
echo.
pause
```

### 2. 手动打包命令

**PowerShell（单行写法，推荐）：**

```powershell
pyinstaller --noconsole --onefile --name YG-DATA --icon "resources\app_icon.ico" --add-data "resources;resources" --hidden-import win32com --hidden-import win32com.client --hidden-import pythoncom --hidden-import pywintypes --hidden-import PySide6.QtNetwork --collect-submodules win32com main.py
```

**cmd（多行写法，续行符 `^`）：**

```cmd
pyinstaller --noconsole --onefile ^
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

> **注意**：PowerShell 的续行符是反引号 `` ` ``，cmd 的续行符是 `^`，两者不能混用。推荐直接用单行命令。

### 3. 打包参数说明

| 参数 | 作用 |
| --- | --- |
| `--noconsole` | 不显示黑色命令行窗口 |
| `--onefile` | 打包为单个 exe 文件 |
| `--name YG-DATA` | 生成的 exe 名称 |
| `--icon` | 设置 exe 图标 |
| `--add-data "resources;resources"` | 把 resources 目录一起打包 |
| `--hidden-import win32com.client` | 必须，否则打包后无法读取 `.doc` |
| `--hidden-import pythoncom` | 必须，COM 初始化依赖 |
| `--hidden-import pywintypes` | 必须，COM 类型库 |
| `--hidden-import PySide6.QtNetwork` | 更新检查依赖 |
| `--collect-submodules win32com` | 收集 win32com 所有子模块 |
| `--exclude-module` | 排除无用模块，压缩体积 |

### 4. 成品位置

- 单文件模式：`dist\YG-DATA.exe`
- 中间文件：`build\`（可随时删除）

### 5. 打包后验证清单

- [ ] 窗口正常打开，有图标
- [ ] 首页卡片正常显示
- [ ] 菜单“计算方法”“帮助”可用
- [ ] 能导入 `.doc` 并提取角度
- [ ] 能计算表面能
- [ ] 能导出 Excel
- [ ] 帮助 → 检查更新可用
- [ ] 帮助 → 使用手册可用

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

在 `main.py` 中设置当前版本号：

```python
app.setApplicationVersion("2.0")
```

### 3. 发布新版本流程

1. 修改 `main.py` 版本号
2. 用 `build.bat` 打包
3. 提交代码到 GitHub
4. 进入仓库 → Releases → Draft a new release
5. Tag 填 `v2.1.0`，填写更新说明，上传 `YG-DATA.exe`
6. Publish release
7. 用户下次启动即收到更新提示

### 4. 核心模块

`core/updater.py` 提供 `UpdateChecker` 类，异步检查更新，不阻塞 UI：

- 信号 `update_available(dict)`：有新版本
- 信号 `up_to_date(str)`：已是最新
- 信号 `check_failed(str)`：检查失败

---

## 九、注意事项

- 程序依赖本机 Office 环境读取 `.doc` 文件
- 建议直接使用 `.doc` 格式，`.docx` 也可被识别
- 配对基于文件名：去掉扩展名后文件名需完全一致
- 手动输入时，样品列可输入任意文本；水接触角与二碘甲烷接触角列仅允许数字
- 删除行按行索引操作，空白行不会被误删
- 导出时自动过滤全空行，保留数值类型
- 更新检查在无网络或 GitHub 不可达时静默失败，不影响正常使用

---

## 十、扩展方式

### 新增计算功能

只需三步：

1. 在 `core/<新功能>/calculator.py` 中编写计算逻辑
2. 在 `views/pages/` 下新建页面类，继承 `BaseCalculatorPage`，设置 `PAGE_TITLE` 与 `PAGE_KEY`
3. 在 `views/main_window.py` 的 `_PAGE_REGISTRY` 中注册该类及描述、图标

首页卡片、菜单项、页面切换将自动生成，无需修改 UI 文件。

### 发布新版本

1. 更新 `main.py` 的 `app.setApplicationVersion("x.y.z")`
2. 运行 `build.bat` 打包
3. 在 GitHub 创建对应的 Release 并上传 exe
4. 用户在下次启动时收到更新提示

---

## 十一、常见问题

### 打包时提示 `Script file '^' does not exist`

在 PowerShell 中误用了 cmd 的续行符 `^`。改用单行命令，或使用反引号 `` ` `` 续行。

### 打包后无法读取 `.doc`

确认已加 `--hidden-import win32com.client`、`--hidden-import pythoncom`、`--hidden-import pywintypes` 和 `--collect-submodules win32com`。

### 打包后 exe 闪退

用 `--console` 代替 `--noconsole` 重新打包，命令行运行即可看到具体错误。

### exe 体积过大

正常现象，PySide6 本身较大。可用 `--exclude-module` 排除无用模块（QtWebEngine、Qt3D、matplotlib、numpy 等）。

### 更新检查返回 403 / 404

- 403：缺 User-Agent 或 API 限流。代码已加 User-Agent，正常不会触发
- 404：用户名或仓库名写错，或仓库是 Private

### 更新检查国内访问慢

可在 `core/updater.py` 里设置超时（`request.setTransferTimeout(8000)`），失败时静默跳过，不影响使用。

---

© 2026 YourOrganization · YG DATA