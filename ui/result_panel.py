# -*- coding: utf-8 -*-
"""
結果面板模組

顯示模擬計算結果。
"""

import tkinter as tk
from tkinter import ttk

from config import FREQUENCY_MHZ


class ResultPanel(ttk.LabelFrame):
    """結果面板"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text=' 📊 模擬結果 ', **kwargs)
        self._result_vars = {}
        self._create_widgets()

    def _create_widgets(self):
        row = 0

        # 基本資訊
        info_frame = ttk.LabelFrame(self, text=' 基本資訊 ')
        info_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1
        self._add_result_row(info_frame, 0, '站 A 海拔', 'm', 'elev1')
        self._add_result_row(info_frame, 1, '站 B 海拔', 'm', 'elev2')
        self._add_result_row(info_frame, 2, '兩站距離', 'km', 'distance')
        self._add_result_row(info_frame, 3, '取樣點數', '點', 'num_samples')

        # LOS 分析
        los_frame = ttk.LabelFrame(self, text=' 視線 (LOS) 分析 ')
        los_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1
        self._add_result_row(los_frame, 0, 'LOS 判定', '', 'los_status')
        self._add_result_row(los_frame, 1, '最大遮蔽高度', 'm', 'max_obstruction')

        # Fresnel 分析
        fresnel_frame = ttk.LabelFrame(self, text=' Fresnel 淨空分析 ')
        fresnel_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1
        self._add_result_row(fresnel_frame, 0, '頻率', 'MHz', 'frequency')
        self._add_result_row(fresnel_frame, 1, '波長', 'm', 'wavelength')
        self._add_result_row(fresnel_frame, 2, '最小淨空比', '', 'min_clearance')
        self._add_result_row(fresnel_frame, 3, 'Fresnel 淨空', '', 'fresnel_status')

        # Fresnel 最差點詳細資訊
        detail_frame = ttk.LabelFrame(self, text=' Fresnel 最差點詳情 ')
        detail_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1
        self._add_result_row(detail_frame, 0, '最差點位置', 'km', 'worst_point_dist')
        self._add_result_row(detail_frame, 1, 'LOS 高度', 'm', 'worst_los_h')
        self._add_result_row(detail_frame, 2, '地形高度', 'm', 'worst_terrain_h')
        self._add_result_row(detail_frame, 3, '淨空量', 'm', 'worst_clearance')
        self._add_result_row(detail_frame, 4, 'Fresnel 半徑', 'm', 'worst_fresnel_r')
        self._add_result_row(detail_frame, 5, 'Fresnel 下邊界', 'm', 'worst_fresnel_lower')
        self._add_result_row(detail_frame, 6, '侵入深度', 'm', 'worst_intrusion')

        # 損耗與功率
        power_frame = ttk.LabelFrame(self, text=' 損耗與接收功率 ')
        power_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1
        self._add_result_row(power_frame, 0, 'FSPL', 'dB', 'fspl')
        self._add_result_row(power_frame, 1, '繞射損耗', 'dB', 'diffraction_loss')
        self._add_result_row(power_frame, 2, '總路徑損耗', 'dB', 'total_loss')
        self._add_result_row(power_frame, 3, '接收功率', 'dBm', 'rx_power')

        # 繞射方法說明
        method_frame = ttk.LabelFrame(self, text=' 繞射模型 ')
        method_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1
        ttk.Label(method_frame,
                  text="方法: Deygout 多刃法\n(ITU-R P.526)\n地球曲率: k=4/3",
                  foreground='gray', font=('Microsoft JhengHei', 8)).grid(
            row=0, column=0, padx=8, pady=4, sticky='w')

        self.columnconfigure(0, weight=1)

    def _add_result_row(self, parent, row, label, unit, key):
        ttk.Label(parent, text=f'{label}:').grid(
            row=row, column=0, padx=4, pady=1, sticky='e')
        var = tk.StringVar(value='—')
        self._result_vars[key] = var
        ttk.Label(parent, textvariable=var,
                  font=('Consolas', 10, 'bold')).grid(
            row=row, column=1, padx=4, pady=1, sticky='w')
        if unit:
            ttk.Label(parent, text=unit, foreground='gray').grid(
                row=row, column=2, padx=2, pady=1, sticky='w')

    def update_results(self, results: dict):
        for key, value in results.items():
            if key in self._result_vars:
                self._result_vars[key].set(str(value))

    def clear_results(self):
        for var in self._result_vars.values():
            var.set('—')
