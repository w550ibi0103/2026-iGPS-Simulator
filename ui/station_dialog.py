# -*- coding: utf-8 -*-
"""
站點載入對話框模組

提供一個彈出視窗，列出所有已定義的站點資訊，
讓使用者選擇後自動填入座標到輸入面板。
站點資料從 stations.json 讀取。
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox


class StationLoaderDialog(tk.Toplevel):
    """
    站點載入對話框

    顯示站點列表，使用者選擇後回傳該站點的座標。
    """

    def __init__(self, parent, stations_file: str, title: str = '選擇站點'):
        """
        Parameters
        ----------
        parent : tk.Widget
            父視窗
        stations_file : str
            stations.json 檔案路徑
        title : str
            對話框標題
        """
        super().__init__(parent)
        self.title(title)
        self.geometry('450x400')
        self.resizable(False, True)

        # 將對話框設為 modal (阻擋父視窗操作)
        self.transient(parent)
        self.grab_set()

        # 結果：使用者選擇的站點 (None = 取消)
        self.result = None

        # 載入站點資料
        self._stations = self._load_stations(stations_file)

        # 建立 UI
        self._create_widgets()

        # 置中顯示
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 400) // 2
        self.geometry(f'+{x}+{y}')

        # 等待關閉
        self.wait_window()

    def _load_stations(self, stations_file: str) -> list:
        """從 JSON 檔案載入站點列表"""
        try:
            with open(stations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showerror('錯誤', f'找不到站點檔案:\n{stations_file}')
            return []
        except json.JSONDecodeError as e:
            messagebox.showerror('錯誤', f'站點檔案格式錯誤:\n{e}')
            return []

    def _create_widgets(self):
        """建立對話框元件"""
        # 說明文字
        ttk.Label(self, text='請選擇一個站點：',
                  font=('Microsoft JhengHei', 10)).pack(
            padx=10, pady=(10, 5), anchor='w')

        # 站點列表容器 (先建立 frame，再在裡面建立 Treeview)
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Treeview — parent 必須是 tree_frame
        columns = ('name', 'lat', 'lon')
        self._tree = ttk.Treeview(
            tree_frame, columns=columns, show='headings',
            selectmode='browse', height=12
        )

        # 設定欄位標題
        self._tree.heading('name', text='站點名稱')
        self._tree.heading('lat', text='緯度 (°N)')
        self._tree.heading('lon', text='經度 (°E)')

        # 設定欄位寬度
        self._tree.column('name', width=160, anchor='w')
        self._tree.column('lat', width=120, anchor='center')
        self._tree.column('lon', width=120, anchor='center')

        # 填入站點資料
        for station in self._stations:
            self._tree.insert('', 'end', values=(
                station['name'],
                f"{station['lat']:.6f}",
                f"{station['lon']:.6f}",
            ))

        # 捲軸 — parent 也必須是 tree_frame
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical',
                                  command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        # 排版 (都在 tree_frame 內)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 按鈕列
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        ttk.Button(btn_frame, text='確定',
                   command=self._on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text='取消',
                   command=self._on_cancel).pack(side=tk.RIGHT, padx=5)

        # 雙擊也可以選擇
        self._tree.bind('<Double-1>', lambda e: self._on_ok())

    def _on_ok(self):
        """確定按鈕"""
        selection = self._tree.selection()
        if not selection:
            messagebox.showwarning('提示', '請先選擇一個站點')
            return

        # 取得選中的站點索引
        item = self._tree.item(selection[0])
        values = item['values']

        # 回傳結果
        self.result = {
            'name': values[0],
            'lat': float(values[1]),
            'lon': float(values[2]),
        }
        self.destroy()

    def _on_cancel(self):
        """取消按鈕"""
        self.result = None
        self.destroy()
