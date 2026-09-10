import json
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


# ==================== 版本号解析 ====================
def parse_version(v):
    """
    把 '2.1.0'、'v2.1.0'、'2.1.0-beta' 解析为 (2, 1, 0)。
    取前 3 段数字，缺位补 0。
    """
    if v is None:
        return (0, 0, 0)
    s = str(v).strip().lstrip("vV")
    parts = []
    for seg in s.split('.'):
        num = ''
        for ch in seg:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


# ==================== 更新检查器 ====================
class UpdateChecker(QObject):
    """
    异步从 GitHub Releases API 拉取最新版本信息。
    信号：
      - update_available(dict)  有新版本
      - up_to_date(str)         已是最新，参数为当前版本
      - check_failed(str)       检查失败，参数为错误信息
    """

    update_available = Signal(dict)
    up_to_date = Signal(str)
    check_failed = Signal(str)

    def __init__(self, current_version, api_url, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.api_url = api_url
        self.nam = QNetworkAccessManager(self)

    def check(self):
        request = QNetworkRequest(QUrl(self.api_url))
        # GitHub API 要求 User-Agent，否则返回 403
        request.setRawHeader(b"User-Agent", b"YG-DATA-UpdateChecker")
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        # 禁用缓存
        request.setAttribute(
            QNetworkRequest.Attribute.CacheLoadControlAttribute,
            QNetworkRequest.CacheLoadControl.AlwaysNetwork,
        )
        # 允许重定向
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        reply = self.nam.get(request)
        reply.finished.connect(lambda: self._on_finished(reply))

    def _on_finished(self, reply):
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.check_failed.emit(reply.errorString())
                return

            raw = bytes(reply.readAll().data())
            data = json.loads(raw.decode('utf-8'))

            remote_version = str(data.get("tag_name", "")).lstrip("vV")
            if not remote_version:
                self.check_failed.emit("GitHub 返回的 Release 缺少 tag_name")
                return

            # 从 assets 里找 .exe 下载链接
            download_url = ""
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    break
            # 没找到 exe，退而给出 release 页面地址
            if not download_url:
                download_url = data.get("html_url", "")

            info = {
                "version": remote_version,
                "download_url": download_url,
                "changelog": data.get("body", "（暂无更新说明）"),
                "release_url": data.get("html_url", ""),
                "force": False,  # 如需强制更新，可在描述里加标记自行解析
            }

            if parse_version(remote_version) > parse_version(self.current_version):
                self.update_available.emit(info)
            else:
                self.up_to_date.emit(self.current_version)

        except Exception as e:
            self.check_failed.emit(str(e))
        finally:
            reply.deleteLater()