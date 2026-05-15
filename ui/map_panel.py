# -*- coding: utf-8 -*-
"""
地圖與剖面圖面板模組 (PyQt6)

上方: 使用 QWebEngineView 嵌入 folium 互動地圖
下方: 嵌入 matplotlib 剖面圖 (使用 FigureCanvasQTAgg)
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QGroupBox, QLabel,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg


class MapPanel(QWidget):
    """地圖與剖面圖面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_widgets()

    def _create_widgets(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # ======== 上方: 嵌入式地圖 (QWebEngineView) ========
        map_group = QGroupBox(' 🗺️ 台灣地圖 ')
        map_layout = QVBoxLayout(map_group)

        self._web_view = QWebEngineView()
        # 初始頁面：顯示等待提示
        self._web_view.setHtml(self._placeholder_html('地圖將在模擬後顯示'))
        map_layout.addWidget(self._web_view)

        splitter.addWidget(map_group)

        # ======== 下方: 剖面圖 (matplotlib) ========
        profile_group = QGroupBox(' 📈 地形剖面圖 ')
        profile_layout = QVBoxLayout(profile_group)

        self._fig = Figure(figsize=(8, 4), dpi=100)
        self._canvas = FigureCanvasQTAgg(self._fig)
        profile_layout.addWidget(self._canvas)

        splitter.addWidget(profile_group)

        # 設定分割比例 (地圖:剖面圖 = 1:2)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # 初始空白剖面圖
        ax = self._fig.add_subplot(111)
        ax.set_facecolor('#D6EAF8')
        ax.text(0.5, 0.5, '剖面圖將在模擬後顯示',
                ha='center', va='center', fontsize=12,
                color='gray', fontfamily='Microsoft JhengHei',
                transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        self._fig.tight_layout()
        self._canvas.draw()

    @property
    def fig(self) -> Figure:
        return self._fig

    def update_map(self, html_content: str):
        """
        在 QWebEngineView 中載入 folium 地圖 HTML

        Parameters
        ----------
        html_content : str
            folium 產生的完整 HTML 字串
        """
        self._web_view.setHtml(html_content)

    def refresh_profile(self):
        self._canvas.draw()

    @staticmethod
    def _placeholder_html(message: str) -> str:
        """產生佔位 HTML 頁面"""
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{
    display: flex; justify-content: center; align-items: center;
    height: 100vh; margin: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    font-family: 'Microsoft JhengHei', sans-serif;
    color: white;
  }}
  .msg {{
    text-align: center; font-size: 18px;
    background: rgba(255,255,255,0.15);
    padding: 30px 50px; border-radius: 16px;
    backdrop-filter: blur(10px);
  }}
</style>
</head><body><div class="msg">🗺️ {message}</div></body></html>"""
