# -*- coding: utf-8 -*-
"""
輸入面板模組 (PyQt6)

提供 PyQt6 介面元件，讓使用者輸入兩站基地台的
經緯度、天線高度、模擬精度、功率參數等。
每站下方有「載入座標」按鈕，可從預定義站點列表快速填入座標。
"""

import os
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QFileDialog,
)

from config import RESOLUTION_OPTIONS, LATERAL_SCAN_WIDTH_OPTIONS
from ui.station_dialog import StationLoaderDialog


# stations.json 路徑 (相對於專案根目錄)
STATIONS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'stations.json'
)


class InputPanel(QWidget):
    """輸入面板"""

    def __init__(self, parent=None, on_simulate_callback=None,
                 initial_dem_path='', on_dem_path_changed_callback=None):
        super().__init__(parent)
        self._callback = on_simulate_callback
        self._on_dem_path_changed_callback = on_dem_path_changed_callback
        self._initial_dem_path = initial_dem_path
        self._dem_ready = False
        self.setFixedWidth(280)
        self._create_widgets()

    def _create_widgets(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # ======== DEM 地形資料 ========
        dem_group = QGroupBox(' DEM 地形資料 ')
        dem_form = QFormLayout(dem_group)

        dem_path_layout = QHBoxLayout()
        self._dem_path_edit = QLineEdit(self._initial_dem_path)
        self._dem_path_edit.setToolTip(self._initial_dem_path)
        self._dem_path_edit.editingFinished.connect(self._on_dem_path_edited)
        dem_path_layout.addWidget(self._dem_path_edit)

        dem_browse_btn = QPushButton('瀏覽...')
        dem_browse_btn.clicked.connect(self._browse_dem_path)
        dem_path_layout.addWidget(dem_browse_btn)

        dem_form.addRow(dem_path_layout)
        main_layout.addWidget(dem_group)

        # ======== 站 A ========
        station_a_group = QGroupBox(' 站 A (發射端) ')
        station_a_form = QFormLayout(station_a_group)

        self._lat1_edit = QLineEdit('25.033')
        station_a_form.addRow('緯度 (°N):', self._lat1_edit)

        self._lon1_edit = QLineEdit('121.565')
        station_a_form.addRow('經度 (°E):', self._lon1_edit)

        self._h_ant1_edit = QLineEdit('30')
        station_a_form.addRow('天線高 (m):', self._h_ant1_edit)

        load_a_btn = QPushButton('📂 載入座標')
        load_a_btn.clicked.connect(lambda: self._load_station('A'))
        station_a_form.addRow(load_a_btn)

        main_layout.addWidget(station_a_group)

        # ======== 站 B ========
        station_b_group = QGroupBox(' 站 B (接收端) ')
        station_b_form = QFormLayout(station_b_group)

        self._lat2_edit = QLineEdit('25.040')
        station_b_form.addRow('緯度 (°N):', self._lat2_edit)

        self._lon2_edit = QLineEdit('121.570')
        station_b_form.addRow('經度 (°E):', self._lon2_edit)

        self._h_ant2_edit = QLineEdit('30')
        station_b_form.addRow('天線高 (m):', self._h_ant2_edit)

        load_b_btn = QPushButton('📂 載入座標')
        load_b_btn.clicked.connect(lambda: self._load_station('B'))
        station_b_form.addRow(load_b_btn)

        main_layout.addWidget(station_b_group)

        # ======== 模擬參數 ========
        sim_group = QGroupBox(' 模擬參數 ')
        sim_form = QFormLayout(sim_group)

        self._resolution_combo = QComboBox()
        for key, desc in RESOLUTION_OPTIONS.items():
            self._resolution_combo.addItem(str(key), key)
        self._resolution_combo.setCurrentIndex(0)  # 預設 20m
        sim_form.addRow('取樣精度 (m):', self._resolution_combo)

        self._scan_width_combo = QComboBox()
        for key, desc in LATERAL_SCAN_WIDTH_OPTIONS.items():
            self._scan_width_combo.addItem(desc, key)
        self._scan_width_combo.setCurrentIndex(0)  # 預設 100m
        sim_form.addRow('側向掃描寬度 (±m):', self._scan_width_combo)

        main_layout.addWidget(sim_group)

        # ======== 功率參數 ========
        power_group = QGroupBox(' 功率參數 ')
        power_form = QFormLayout(power_group)

        self._tx_power_edit = QLineEdit('40')
        power_form.addRow('發射功率 (dBm):', self._tx_power_edit)

        self._tx_gain_edit = QLineEdit('6')
        power_form.addRow('Tx 增益 (dBi):', self._tx_gain_edit)

        self._rx_gain_edit = QLineEdit('6')
        power_form.addRow('Rx 增益 (dBi):', self._rx_gain_edit)

        main_layout.addWidget(power_group)

        # ======== 模擬按鈕 ========
        self._simulate_btn = QPushButton('🚀 開始模擬')
        self._simulate_btn.setMinimumHeight(36)
        self._simulate_btn.setStyleSheet(
            'QPushButton { font-size: 14px; font-weight: bold; }')
        self._simulate_btn.clicked.connect(self._on_simulate)
        self._simulate_btn.setEnabled(False)
        main_layout.addWidget(self._simulate_btn)

        # ======== 狀態列 ========
        self._status_label = QLabel('就緒')
        self._status_label.setStyleSheet('color: gray;')
        main_layout.addWidget(self._status_label)

        # 彈性空間
        main_layout.addStretch()

    def _browse_dem_path(self):
        """開啟檔案選擇對話框，選擇 DEM GeoTIFF 檔案"""
        start_dir = os.path.dirname(self._dem_path_edit.text())
        path, _ = QFileDialog.getOpenFileName(
            self, '選擇 DEM 檔案', start_dir, 'GeoTIFF (*.tif *.tiff)')
        if path:
            self._dem_path_edit.setText(path)
            self._notify_dem_path_changed()

    def _on_dem_path_edited(self):
        """使用者手動編輯路徑欄位後 (按 Enter 或失焦) 觸發驗證"""
        self._notify_dem_path_changed()

    def _notify_dem_path_changed(self):
        if self._on_dem_path_changed_callback:
            self._on_dem_path_changed_callback(self._dem_path_edit.text())

    def set_dem_status(self, is_valid: bool, message: str = ''):
        """
        依 DEM 載入結果更新路徑方框顏色與模擬按鈕狀態

        Parameters
        ----------
        is_valid : bool
            DEM 是否成功載入
        message : str
            失敗時的錯誤訊息，會顯示於 tooltip
        """
        if is_valid:
            self._dem_path_edit.setStyleSheet(
                'QLineEdit { background-color: #D5F5E3; }')
            self._dem_path_edit.setToolTip(self._dem_path_edit.text())
        else:
            self._dem_path_edit.setStyleSheet(
                'QLineEdit { background-color: #FADBD8; }')
            self._dem_path_edit.setToolTip(
                message or '找不到有效的 DEM 檔案')
        self._dem_ready = is_valid
        self._simulate_btn.setEnabled(is_valid)

    def _load_station(self, station: str):
        """
        開啟站點選擇對話框，並將選中的座標填入對應的欄位

        Parameters
        ----------
        station : str
            'A' 或 'B'，指定要填入哪一站的座標
        """
        dialog = StationLoaderDialog(
            self.window(),
            STATIONS_FILE,
            title=f'選擇站 {station} 的座標'
        )

        if dialog.exec():
            result = dialog.result
            if result is not None:
                if station == 'A':
                    self._lat1_edit.setText(str(result['lat']))
                    self._lon1_edit.setText(str(result['lon']))
                else:
                    self._lat2_edit.setText(str(result['lat']))
                    self._lon2_edit.setText(str(result['lon']))

    def _on_simulate(self):
        self._status_label.setText('⏳ 模擬中...')
        self._status_label.setStyleSheet('color: #E67E22;')
        self._simulate_btn.setEnabled(False)
        # 使用 QTimer 讓 UI 有機會更新後再執行計算
        QTimer.singleShot(50, self._callback)

    def get_parameters(self) -> dict:
        return {
            'lat1': float(self._lat1_edit.text()),
            'lon1': float(self._lon1_edit.text()),
            'lat2': float(self._lat2_edit.text()),
            'lon2': float(self._lon2_edit.text()),
            'h_ant1': float(self._h_ant1_edit.text()),
            'h_ant2': float(self._h_ant2_edit.text()),
            'resolution_m': int(self._resolution_combo.currentText()),
            'scan_width_m': self._scan_width_combo.currentData(),
            'tx_power_dbm': float(self._tx_power_edit.text()),
            'tx_gain_dbi': float(self._tx_gain_edit.text()),
            'rx_gain_dbi': float(self._rx_gain_edit.text()),
        }

    def set_status(self, msg: str):
        self._status_label.setText(msg)
        if '✅' in msg:
            self._status_label.setStyleSheet('color: #27AE60;')
        elif '❌' in msg:
            self._status_label.setStyleSheet('color: #E74C3C;')
        else:
            self._status_label.setStyleSheet('color: gray;')
        self._simulate_btn.setEnabled(self._dem_ready)
