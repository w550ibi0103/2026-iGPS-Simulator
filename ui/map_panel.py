# -*- coding: utf-8 -*-
"""
地圖與剖面圖面板模組

上方: 互動地圖 (存成 HTML 檔，用系統瀏覽器開啟)
下方: 嵌入 matplotlib 剖面圖 (使用 FigureCanvasTkAgg)

Note: tkhtmlview 不支援 JavaScript，無法正確渲染 folium 地圖。
      改為存成 HTML 檔，用瀏覽器開啟以獲得完整互動功能。
"""

import os
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class MapPanel(ttk.Frame):
    """地圖與剖面圖面板"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # 地圖 HTML 暫存檔路徑 (固定檔名，覆蓋更新)
        self._map_html_path = os.path.join(
            tempfile.gettempdir(), 'igps_simulator_map.html'
        )
        self._create_widgets()

    def _create_widgets(self):
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # ======== 上方: 地圖控制面板 ========
        map_frame = ttk.LabelFrame(paned, text=' 🗺️ 台灣地圖 ')
        paned.add(map_frame, weight=1)

        # 地圖狀態 + 開啟按鈕
        map_inner = ttk.Frame(map_frame)
        map_inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._map_status_var = tk.StringVar(value='地圖將在模擬後產生')
        ttk.Label(map_inner, textvariable=self._map_status_var,
                  font=('Microsoft JhengHei', 10)).pack(pady=(20, 10))

        self._open_map_btn = ttk.Button(
            map_inner, text='🌐 在瀏覽器中開啟地圖',
            command=self._open_map_in_browser, state='disabled'
        )
        self._open_map_btn.pack(pady=5)

        # 提示文字
        ttk.Label(map_inner,
                  text='（地圖使用系統瀏覽器開啟，支援完整平移與縮放功能）',
                  foreground='gray', font=('Microsoft JhengHei', 8)
                  ).pack(pady=(0, 10))

        # ======== 下方: 剖面圖 ========
        profile_frame = ttk.LabelFrame(paned, text=' 📈 地形剖面圖 ')
        paned.add(profile_frame, weight=3)

        self._fig = Figure(figsize=(8, 4), dpi=100)
        self._canvas = FigureCanvasTkAgg(self._fig, master=profile_frame)
        self._canvas.get_tk_widget().pack(
            fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 初始空白圖
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
        儲存地圖 HTML 並自動在瀏覽器中開啟

        Parameters
        ----------
        html_content : str
            folium 產生的完整 HTML 字串
        """
        try:
            # 將 folium HTML 存為完整的獨立 HTML 檔案
            with open(self._map_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self._map_status_var.set('✅ 地圖已產生，已在瀏覽器中開啟')
            self._open_map_btn.configure(state='normal')

            # 自動在瀏覽器中開啟
            webbrowser.open(f'file:///{self._map_html_path}')

        except Exception as e:
            self._map_status_var.set(f'❌ 地圖產生失敗: {e}')

    def _open_map_in_browser(self):
        """手動在瀏覽器中開啟地圖"""
        if os.path.exists(self._map_html_path):
            webbrowser.open(f'file:///{self._map_html_path}')

    def refresh_profile(self):
        self._canvas.draw()
