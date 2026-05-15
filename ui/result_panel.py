# -*- coding: utf-8 -*-
"""
結果面板模組 (PyQt6)

顯示模擬計算結果。
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QScrollArea,
)
from PyQt6.QtGui import QFont

from config import FREQUENCY_MHZ


class ResultPanel(QWidget):
    """結果面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self._result_labels = {}
        self._create_widgets()

    def _create_widgets(self):
        # 使用 QScrollArea 包裝，避免結果太多時溢出
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer_layout.addWidget(scroll)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)
        scroll.setWidget(container)

        # 標題
        title = QLabel('📊 模擬結果')
        title.setFont(QFont('Microsoft JhengHei', 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # 基本資訊
        info_group = QGroupBox(' 基本資訊 ')
        info_form = QFormLayout(info_group)
        self._add_result_row(info_form, '站 A 海拔 (m)', 'm', 'elev1')
        self._add_result_row(info_form, '站 B 海拔 (m)', 'm', 'elev2')
        self._add_result_row(info_form, '兩站距離 (km)', 'km', 'distance')
        self._add_result_row(info_form, '取樣點數', '點', 'num_samples')
        main_layout.addWidget(info_group)

        # LOS 分析
        los_group = QGroupBox(' 視線 (LOS) 分析 ')
        los_form = QFormLayout(los_group)
        self._add_result_row(los_form, 'LOS 判定', '', 'los_status')
        self._add_result_row(los_form, '最大遮蔽高度 (m)', 'm', 'max_obstruction')
        main_layout.addWidget(los_group)

        # Fresnel 分析
        fresnel_group = QGroupBox(' Fresnel 淨空分析 ')
        fresnel_form = QFormLayout(fresnel_group)
        self._add_result_row(fresnel_form, '頻率 (MHz)', 'MHz', 'frequency')
        self._add_result_row(fresnel_form, '波長 (m)', 'm', 'wavelength')
        self._add_result_row(fresnel_form, '最小淨空比', '', 'min_clearance')
        self._add_result_row(fresnel_form, 'Fresnel 淨空', '', 'fresnel_status')
        main_layout.addWidget(fresnel_group)

        # Fresnel 最差點詳細資訊
        detail_group = QGroupBox(' Fresnel 最差點詳情 ')
        detail_form = QFormLayout(detail_group)
        self._add_result_row(detail_form, '最差點位置 (km)', 'km', 'worst_point_dist')
        self._add_result_row(detail_form, 'LOS 高度 (m)', 'm', 'worst_los_h')
        self._add_result_row(detail_form, '地形高度 (m)', 'm', 'worst_terrain_h')
        self._add_result_row(detail_form, '淨空量 (m)', 'm', 'worst_clearance')
        self._add_result_row(detail_form, 'Fresnel 半徑 (m)', 'm', 'worst_fresnel_r')
        self._add_result_row(detail_form, 'Fresnel 下邊界 (m)', 'm', 'worst_fresnel_lower')
        self._add_result_row(detail_form, '侵入深度 (m)', 'm', 'worst_intrusion')
        main_layout.addWidget(detail_group)

        # 損耗與功率
        power_group = QGroupBox(' 損耗與接收功率 ')
        power_form = QFormLayout(power_group)
        self._add_result_row(power_form, '自由空間路徑損耗 (dB)', 'dB', 'fspl')
        self._add_result_row(power_form, '繞射損耗 (dB)', 'dB', 'diffraction_loss')
        self._add_result_row(power_form, '總路徑損耗 (dB)', 'dB', 'total_loss')
        self._add_result_row(power_form, '接收功率 (dBm)', 'dBm', 'rx_power')
        main_layout.addWidget(power_group)

        # Fresnel 說明
        fresnel_explanation_group = QGroupBox(' Fresnel 說明 ')
        fresnel_explanation_layout = QVBoxLayout(fresnel_explanation_group)
        fresnel_explanation_label = QLabel("Fresnel 下邊界=LOS高度-Fresnel半徑\n侵入深度=Fresnel下邊界-地形高度")
        fresnel_explanation_label.setStyleSheet('color: gray; font-size: 9px;')
        fresnel_explanation_label.setFont(QFont('Microsoft JhengHei', 8))
        fresnel_explanation_layout.addWidget(fresnel_explanation_label)
        main_layout.addWidget(fresnel_explanation_group)

        # 繞射方法說明
        method_group = QGroupBox(' 繞射模型 ')
        method_layout = QVBoxLayout(method_group)
        method_label = QLabel(
            "方法: Deygout 多刃法\n(ITU-R P.526)\n地球曲率: k=4/3\n")
        method_label.setStyleSheet('color: gray; font-size: 9px;')
        method_label.setFont(QFont('Microsoft JhengHei', 8))
        method_layout.addWidget(method_label)
        main_layout.addWidget(method_group)

        main_layout.addStretch()

    def _add_result_row(self, form_layout: QFormLayout,
                        label: str, unit: str, key: str):
        """新增一行結果欄位"""
        value_label = QLabel('—')
        value_label.setFont(QFont('Consolas', 10, QFont.Weight.Bold))

        if unit:
            # 將值與單位並排顯示
            row_widget = QWidget()
            row_layout = QFormLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            # 直接用文字組合
            display_text = f'— {unit}'
            value_label.setText('—')

            unit_label = QLabel(unit)
            unit_label.setStyleSheet('color: gray; font-size: 9px;')

            form_layout.addRow(f'{label}:', value_label)
        else:
            form_layout.addRow(f'{label}:', value_label)

        self._result_labels[key] = (value_label, unit)

    def update_results(self, results: dict):
        for key, value in results.items():
            if key in self._result_labels:
                label, unit = self._result_labels[key]
                label.setText(str(value))

    def clear_results(self):
        for label, unit in self._result_labels.values():
            label.setText('—')
