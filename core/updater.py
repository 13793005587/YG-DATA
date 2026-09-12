import json
import logging

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from core.config import UPDATE_FORCE_MARKER

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_MS = 12000


# ==================== 版本号解析 ====================
def parse_version(v):
    """
    把 '2.1.0'、'v2.1.0'、'2.1.0-beta' 解析为 (2, 1, 0)。

    取前 3 段数字，缺位补 0；只剥掉**一个** v/V 前缀。
    注意：预发布版本（2.1.0-beta）与正式版 2.1.0 视为相同版本，
    即发布 beta 时不会弹出更新提示（保守行为）。
    """
    if v is None or v == "":
        return (0, 0, 0)
    s = str(v).strip()
    if s[:1] in ("v", "V"):
        s = s[1:]
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
      - finished()              本次检查结束（成功或失败都会发出）
    """

    update_available = Signal(dict)
    up_to_date = Signal(str)
    check_failed = Signal(str)
    finished = Signal()

    def __init__(self, current_version, api_url, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.api_url = api_url
        self.nam = QNetworkAccessManager(self)
        self._reply = None

    @property
    def in_progress(self):
        return self._reply is not None

    def check(self):
        """发起一次检查。已在检查中时直接忽略，避免重复请求。"""
        if self._reply is not None:
            logger.debug("上一次检查尚未结束，忽略本次请求")
            return

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
        # 超时：网络挂起时必须能失败，否则 UI 状态会永久卡在"检查中"
        try:
            request.setTransferTimeout(REQUEST_TIMEOUT_MS)
        except AttributeError:  # pragma: no cover - 旧版 Qt 无此接口
            logger.debug("当前 Qt 版本不支持 setTransferTimeout")

        reply = self.nam.get(request)
        self._reply = reply
        reply.finished.connect(lambda: self._on_finished(reply))

    def _on_finished(self, reply):
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                message = reply.errorString()
                logger.warning("检查更新失败：%s", message)
                self.check_failed.emit(message)
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
                if str(asset.get("name", "")).lower().endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    break
            # 没找到 exe，退而给出 release 页面地址
            if not download_url:
                download_url = data.get("html_url", "")

            body = data.get("body") or "（暂无更新说明）"
            info = {
                "version": remote_version,
                "download_url": download_url,
                "changelog": body,
                "release_url": data.get("html_url", ""),
                # 在 Release 描述里写入标记即可开启强制更新
                "force": UPDATE_FORCE_MARKER in body,
            }

            if parse_version(remote_version) > parse_version(self.current_version):
                self.update_available.emit(info)
            else:
                self.up_to_date.emit(self.current_version)

        except Exception as e:  # noqa: BLE001 - 解析异常同样属于"检查失败"
            logger.exception("解析更新信息失败")
            self.check_failed.emit(str(e))
        finally:
            reply.deleteLater()
            self._reply = None
            self.finished.emit()
