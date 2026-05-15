# -*- coding: utf-8 -*-
"""
站點載入對話框模組 (PyQt6)

提供一個彈出視窗，列出所有已定義的站點資訊，
讓使用者選擇後自動填入座標到輸入面板。
站點資料從 stations.json 讀取。
"""

import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView,
)
from PyQt6.QtGui import QFont


class StationLoaderDialog(QDialog):
    """
    站點載入對話框

    顯示站點列表，使用者選擇後回傳該站點的座標。
    """

    def __init__(self, parent, stations_file: str, title: str = '選擇站點'):
        """
        Parameters
        ----------
        parent : QWidget
            父視窗
        stations_file : str
            stations.json 檔案路徑
        title : str
            對話框標題
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(480, 420)
        self.setModal(True)

        # 結果：使用者選擇的站點 (None = 取消)
        self.result = None

        # 載入站點資料
        self._stations = self._load_stations(stations_file)

        # 建立 UI
        self._create_widgets()

    def _load_stations(self, stations_file: str) -> list:
        """從 JSON 檔案載入站點列表"""
        try:
            with open(stations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(
                self, '錯誤', f'找不到站點檔案:\n{stations_file}')
            return []
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self, '錯誤', f'站點檔案格式錯誤:\n{e}')
            return []

    def _create_widgets(self):
        """建立對話框元件"""
        layout = QVBoxLayout(self)

        # 說明文字
        hint_label = QLabel('請選擇一個站點：')
        hint_label.setFont(QFont('Microsoft JhengHei', 10))
        layout.addWidget(hint_label)

        # 站點表格
        self._table = QTableWidget(len(self._stations), 3)
        self._table.setHorizontalHeaderLabels(['站點名稱', '緯度 (°N)', '經度 (°E)'])
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        # 自動調整欄寬
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        # 填入站點資料
        for i, station in enumerate(self._stations):
            name_item = QTableWidgetItem(station['name'])
            lat_item = QTableWidgetItem(f"{station['lat']:.6f}")
            lon_item = QTableWidgetItem(f"{station['lon']:.6f}")

            lat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            lon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self._table.setItem(i, 0, name_item)
            self._table.setItem(i, 1, lat_item)
            self._table.setItem(i, 2, lon_item)

        # 雙擊也可以選擇
        self._table.doubleClicked.connect(self._on_ok)

        layout.addWidget(self._table)

        # 按鈕列
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton('確定')
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def _on_ok(self):
        """確定按鈕"""
        selected = self._table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, '提示', '請先選擇一個站點')
            return

        row = selected[0].row()
        self.result = {
            'name': self._table.item(row, 0).text(),
            'lat': float(self._table.item(row, 1).text()),
            'lon': float(self._table.item(row, 2).text()),
        }
        self.accept()
