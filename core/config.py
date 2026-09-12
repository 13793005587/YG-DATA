"""应用级常量：版本号与更新源在这里单点定义，其余模块一律从这里取值。

新增/修改版本号只改本文件的 APP_VERSION。
"""

APP_NAME = "YG DATA"
APP_VERSION = "2.1.0"          # 三段式：发新版时只改这一行
ORG_NAME = "YG Lab"
ORG_DOMAIN = "yg-lab.local"

COPYRIGHT = "© 2026 YG Lab"

# ---------------- 更新源 ----------------
# 改成你自己的 GitHub 用户名和仓库名
GITHUB_OWNER = "13793005587"
GITHUB_REPO = "YG-DATA"
UPDATE_API_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)

# 在 Release 描述里写入该标记即可开启「强制更新」（不显示「稍后再说」）
UPDATE_FORCE_MARKER = "<!-- force-update -->"
