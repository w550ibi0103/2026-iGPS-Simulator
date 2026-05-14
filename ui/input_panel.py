# -*- coding: utf-8 -*-
"""
輸入面板模組

提供 Tkinter 介面元件，讓使用者輸入兩站基地台的
經緯度、天線高度、模擬精度、功率參數等。
"""

import tkinter as tk
from tkinter import ttk

from config import RESOLUTION_OPTIONS


class InputPanel(ttk.LabelFrame):
    """輸入面板"""

    def __init__(self, parent, on_simulate_callback, **kwargs):
        super().__init__(parent, text=' 📡 參數設定 ', **kwargs)
        self._callback = on_simulate_callback
        self._create_widgets()

    def _create_widgets(self):
        row = 0

        # ======== 站 A ========
        station_a_frame = ttk.LabelFrame(self, text=' 站 A (發射端) ')
        station_a_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1

        ttk.Label(station_a_frame, text='緯度 (°N):').grid(
            row=0, column=0, padx=4, pady=2, sticky='e')
        self.lat1_var = tk.StringVar(value='25.033')
        ttk.Entry(station_a_frame, textvariable=self.lat1_var,
                  width=14).grid(row=0, column=1, padx=4, pady=2)

        ttk.Label(station_a_frame, text='經度 (°E):').grid(
            row=1, column=0, padx=4, pady=2, sticky='e')
        self.lon1_var = tk.StringVar(value='121.565')
        ttk.Entry(station_a_frame, textvariable=self.lon1_var,
                  width=14).grid(row=1, column=1, padx=4, pady=2)

        ttk.Label(station_a_frame, text='天線高 (m):').grid(
            row=2, column=0, padx=4, pady=2, sticky='e')
        self.h_ant1_var = tk.StringVar(value='30')
        ttk.Entry(station_a_frame, textvariable=self.h_ant1_var,
                  width=14).grid(row=2, column=1, padx=4, pady=2)

        # ======== 站 B ========
        station_b_frame = ttk.LabelFrame(self, text=' 站 B (接收端) ')
        station_b_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1

        ttk.Label(station_b_frame, text='緯度 (°N):').grid(
            row=0, column=0, padx=4, pady=2, sticky='e')
        self.lat2_var = tk.StringVar(value='25.040')
        ttk.Entry(station_b_frame, textvariable=self.lat2_var,
                  width=14).grid(row=0, column=1, padx=4, pady=2)

        ttk.Label(station_b_frame, text='經度 (°E):').grid(
            row=1, column=0, padx=4, pady=2, sticky='e')
        self.lon2_var = tk.StringVar(value='121.570')
        ttk.Entry(station_b_frame, textvariable=self.lon2_var,
                  width=14).grid(row=1, column=1, padx=4, pady=2)

        ttk.Label(station_b_frame, text='天線高 (m):').grid(
            row=2, column=0, padx=4, pady=2, sticky='e')
        self.h_ant2_var = tk.StringVar(value='30')
        ttk.Entry(station_b_frame, textvariable=self.h_ant2_var,
                  width=14).grid(row=2, column=1, padx=4, pady=2)

        # ======== 模擬參數 ========
        sim_frame = ttk.LabelFrame(self, text=' 模擬參數 ')
        sim_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1

        ttk.Label(sim_frame, text='取樣精度:').grid(
            row=0, column=0, padx=4, pady=2, sticky='e')
        self.resolution_var = tk.StringVar(value='20')
        ttk.Combobox(
            sim_frame, textvariable=self.resolution_var,
            values=list(RESOLUTION_OPTIONS.keys()),
            width=12, state='readonly'
        ).grid(row=0, column=1, padx=4, pady=2)
        ttk.Label(sim_frame, text='公尺').grid(
            row=0, column=2, padx=2, pady=2, sticky='w')

        # ======== 功率參數 ========
        power_frame = ttk.LabelFrame(self, text=' 功率參數 ')
        power_frame.grid(row=row, column=0, padx=8, pady=4, sticky='ew')
        row += 1

        ttk.Label(power_frame, text='發射功率 (dBm):').grid(
            row=0, column=0, padx=4, pady=2, sticky='e')
        self.tx_power_var = tk.StringVar(value='40')
        ttk.Entry(power_frame, textvariable=self.tx_power_var,
                  width=14).grid(row=0, column=1, padx=4, pady=2)

        ttk.Label(power_frame, text='Tx 增益 (dBi):').grid(
            row=1, column=0, padx=4, pady=2, sticky='e')
        self.tx_gain_var = tk.StringVar(value='6')
        ttk.Entry(power_frame, textvariable=self.tx_gain_var,
                  width=14).grid(row=1, column=1, padx=4, pady=2)

        ttk.Label(power_frame, text='Rx 增益 (dBi):').grid(
            row=2, column=0, padx=4, pady=2, sticky='e')
        self.rx_gain_var = tk.StringVar(value='6')
        ttk.Entry(power_frame, textvariable=self.rx_gain_var,
                  width=14).grid(row=2, column=1, padx=4, pady=2)

        # ======== 模擬按鈕 ========
        self.simulate_btn = ttk.Button(
            self, text='🚀 開始模擬', command=self._on_simulate)
        self.simulate_btn.grid(row=row, column=0, padx=8, pady=10, sticky='ew')
        row += 1

        # ======== 狀態列 ========
        self.status_var = tk.StringVar(value='就緒')
        ttk.Label(self, textvariable=self.status_var,
                  foreground='gray').grid(
            row=row, column=0, padx=8, pady=2, sticky='w')

        self.columnconfigure(0, weight=1)

    def _on_simulate(self):
        self.status_var.set('⏳ 模擬中...')
        self.simulate_btn.configure(state='disabled')
        self.after(50, self._callback)

    def get_parameters(self) -> dict:
        return {
            'lat1': float(self.lat1_var.get()),
            'lon1': float(self.lon1_var.get()),
            'lat2': float(self.lat2_var.get()),
            'lon2': float(self.lon2_var.get()),
            'h_ant1': float(self.h_ant1_var.get()),
            'h_ant2': float(self.h_ant2_var.get()),
            'resolution_m': int(self.resolution_var.get()),
            'tx_power_dbm': float(self.tx_power_var.get()),
            'tx_gain_dbi': float(self.tx_gain_var.get()),
            'rx_gain_dbi': float(self.rx_gain_var.get()),
        }

    def set_status(self, msg: str):
        self.status_var.set(msg)
        self.simulate_btn.configure(state='normal')
