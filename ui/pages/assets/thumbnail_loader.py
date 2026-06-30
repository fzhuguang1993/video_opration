# ui/pages/assets/thumbnail_loader.py
"""缩略图异步加载器"""
import requests
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QObject, QThread, Signal


class ImageLoader(QObject):
    """后台线程加载图片"""
    loaded = Signal(str, QImage)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            resp = requests.get(self.url, timeout=10)
            if resp.status_code == 200:
                img = QImage()
                img.loadFromData(resp.content)
                if not img.isNull():
                    self.loaded.emit(self.url, img)
        except Exception:
            pass


class ThumbnailManager:
    """缩略图管理器 - 管理异步加载和缓存"""

    def __init__(self):
        self._cache = {}
        self._threads = {}

    def load(self, url: str, callback):
        if url in self._cache:
            callback(self._cache[url])
            return

        loader = ImageLoader(url)
        thread = QThread()
        loader.moveToThread(thread)

        def on_loaded(loaded_url, img):
            self._cache[loaded_url] = img
            callback(img)
            thread.quit()

        loader.loaded.connect(on_loaded)
        thread.started.connect(loader.run)
        thread.finished.connect(thread.deleteLater)

        self._threads[url] = (thread, loader)
        thread.start()


thumb_manager = ThumbnailManager()
