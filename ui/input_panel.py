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
    QWidget, QVBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel,
)

from config import RESOLUTION_OPTIONS
from ui.station_dialog import StationLoaderDialog


# stations.json 路徑 (相對於專案根目錄)
STATIONS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'stations.json'
)


class InputPanel(QWidget):
    """輸入面板"""

    def __init__(self, parent=None, on_simulate_callback=None):
        super().__init__(parent)
        self._callback = on_simulate_callback
        self.setFixedWidth(280)
        self._create_widgets()

    def _create_widgets(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

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
        main_layout.addWidget(self._simulate_btn)

        # ======== 狀態列 ========
        self._status_label = QLabel('就緒')
        self._status_label.setStyleSheet('color: gray;')
        main_layout.addWidget(self._status_label)

        # 彈性空間
        main_layout.addStretch()

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
        self._simulate_btn.setEnabled(True)
