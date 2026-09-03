====================================================================
 表面能计算软件 (Surface Energy Calculator)
 项目说明文档 (README)
====================================================================

一、项目简介
本软件是一款基于 PySide6 开发的桌面应用程序，主要用于处理接触角实验数据。它能够通过导入实验仪器导出的 Word (DOC) 报告文件，自动提取接触角平均值，并利用 Owens-Wendt (OWRK) 模型计算固体表面能，最终将计算结果导出为格式化的 Excel 表格。

二、主要功能
1. 数据导入与解析：
   - 支持读取旧版 Word (.doc) 格式文件，通过后台调用 Word 或 WPS 进行静默提取，无弹窗、无闪烁。
   - 自动从报告表格中提取关键字段“平均角度”。
   - 采用多线程 (QThread) 提取数据，提取过程中显示进度弹窗并禁用其他按钮，防止界面卡死。
2. 智能数据配对：
   - 通过提取文件名中的核心标识（如数字“1393”，或字母“BJ”），自动将水滴角文件（如 1393.doc）与对应的二碘甲烷文件（如 1393-I.doc）进行配对，完全不受导入顺序影响。
3. 表面能计算：
   - 内置 OWRK 计算模型（见 core/owrk_calculator.py），计算极性分量、色散分量和总表面能。
4. 数据展示与导出：
   - 主界面表格展示（表头为：文件名 | 水接触角 | 二碘甲烷接触角 | 极性分量 | 色散分量 | 估值方法 | 表面能）。
   - 支持将当前表格内容一键导出为 Excel (.xlsx) 文件。

三、技术栈
- 开发语言：Python 3.x
- GUI 框架：PySide6 (Qt for Python) + Qt Designer
- 数据处理：Pandas
- 文件解析：python-docx (用于读取docx，代码已兼容)，win32com (用于后台调用 Word/WPS 读取 .doc)
- 打包工具：PyInstaller

四、项目结构
YG-DATA/
├── main.py                     # 程序入口
├── ui/
│   ├── main_window.ui          # Qt Designer 设计文件
│   └── main_window_ui.py       # 由 UI 文件生成的 Python 代码
├── views/
│   └── main_window.py          # 主窗口逻辑代码（包含多线程 Worker）
├── core/
│   ├── data_processor.py       # 数据提取、配对、计算、导出逻辑
│   └── owrk_calculator.py      # OWRK 表面能计算公式
├── data/                       # 存放数据文件
└── .venv/                      # 虚拟环境

五、安装与运行
1. 创建虚拟环境并激活（可选）
2. 安装所需依赖：
   pip install pyside6 pandas openpyxl python-docx pywin32
3. 运行软件：
   python main.py

六、使用说明
1. 点击“导入水滴角”，选择所有水滴角的 .doc 文件。
2. 点击“导入二碘甲烷角度”，选择所有二碘甲烷的 .doc 文件。
3. 点击“计算表面能”，软件自动根据文件名进行配对并计算，结果展示在表格中。
4. 点击“导出.xlsx文件”，选择保存路径即可导出计算结果。

七、打包说明 (Windows环境)
使用 PyInstaller 打包为单个可执行文件：
pyinstaller --noconsole --onefile --hidden-import pywin32 --name 表面能计算软件 main.py

注意：
- 必须使用 `--hidden-import pywin32`，否则打包后的程序无法读取 .doc 文件。
- 目标电脑必须安装 Microsoft Word 或 WPS 才能正常使用导入功能。

八、注意事项
- 程序依赖本机 Office 环境读取 .doc 文件。
- 建议直接使用 `.doc` 格式，如果使用 `.docx` 也可以被识别。
- 智能配对基于文件名（优先提取最长数字，无数字则提取字母），请保证配对文件的核心命名相同。