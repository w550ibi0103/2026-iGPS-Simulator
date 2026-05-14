# -*- coding: utf-8 -*-
"""
地圖與剖面圖面板模組

上方: 嵌入 folium 互動地圖 (使用 tkhtmlview)
下方: 嵌入 matplotlib 剖面圖 (使用 FigureCanvasTkAgg)
"""

import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class MapPanel(ttk.Frame):
    """地圖與剖面圖面板"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_widgets()

    def _create_widgets(self):
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 上方: 互動地圖
        map_frame = ttk.LabelFrame(paned, text=' 🗺️ 台灣地圖 ')
        paned.add(map_frame, weight=1)

        try:
            from tkhtmlview import HTMLScrolledText
            self._map_widget = HTMLScrolledText(
                map_frame,
                html='<p style="color:gray;text-align:center;">地圖將在模擬後顯示</p>')
            self._map_widget.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
            self._use_html_widget = True
        except ImportError:
            self._map_widget = tk.Text(map_frame, height=10, state='disabled')
            self._map_widget.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
            self._use_html_widget = False

        # 下方: 剖面圖
        profile_frame = ttk.LabelFrame(paned, text=' 📈 地形剖面圖 ')
        paned.add(profile_frame, weight=1)

        self._fig = Figure(figsize=(8, 3.5), dpi=100)
        self._canvas = FigureCanvasTkAgg(self._fig, master=profile_frame)
        self._canvas.get_tk_widget().pack(
            fill=tk.BOTH, expand=True, padx=4, pady=4)

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
        if self._use_html_widget:
            self._map_widget.set_html(html_content)
        else:
            self._map_widget.configure(state='normal')
            self._map_widget.delete('1.0', tk.END)
            self._map_widget.insert('1.0', '[需要 tkhtmlview]\npip install tkhtmlview')
            self._map_widget.configure(state='disabled')

    def refresh_profile(self):
        self._canvas.draw()
