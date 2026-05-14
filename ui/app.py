# -*- coding: utf-8 -*-
"""
主視窗模組 — iGPS 模擬器

整合所有模組，提供三欄式 Tkinter 介面：
  左欄: 輸入面板
  中欄: 地圖 + 剖面圖
  右欄: 結果面板
"""

import tkinter as tk
from tkinter import ttk, messagebox
import traceback

from config import FREQUENCY_MHZ, WAVELENGTH_M, DEM_PATH
from core.dem_loader import DEMLoader
from core.coordinate import CoordinateConverter
from core.terrain_profile import TerrainProfiler
from core.earth_curvature import EarthCurvature
from core.los_analysis import LOSAnalyzer
from core.fresnel import FresnelCalculator
from core.diffraction import DiffractionCalculator
from core.link_budget import LinkBudgetCalculator
from visualization.profile_plot import ProfilePlotter
from visualization.map_view import MapViewer
from ui.input_panel import InputPanel
from ui.result_panel import ResultPanel
from ui.map_panel import MapPanel


class SimulatorApp:
    """iGPS 模擬器主視窗"""

    WINDOW_TITLE = 'iGPS 無線電傳播模擬器 — 台灣地形'
    WINDOW_MIN_SIZE = (1200, 750)

    def __init__(self):
        self._root = tk.Tk()
        self._root.title(self.WINDOW_TITLE)
        self._root.minsize(*self.WINDOW_MIN_SIZE)
        try:
            self._root.state('zoomed')
        except tk.TclError:
            pass

        self._init_core_modules()
        self._create_ui()

    def _init_core_modules(self):
        """初始化所有核心計算模組 (依賴注入)"""
        self._dem_loader = DEMLoader(DEM_PATH)
        self._coord_converter = CoordinateConverter()
        self._terrain_profiler = TerrainProfiler(
            self._dem_loader, self._coord_converter)
        self._earth_curvature = EarthCurvature()
        self._los_analyzer = LOSAnalyzer(self._earth_curvature)
        self._fresnel_calc = FresnelCalculator(
            wavelength=WAVELENGTH_M, earth_curvature=self._earth_curvature)
        self._diffraction_calc = DiffractionCalculator(
            wavelength=WAVELENGTH_M, earth_curvature=self._earth_curvature)
        self._link_budget_calc = LinkBudgetCalculator(
            frequency_mhz=FREQUENCY_MHZ)
        self._profile_plotter = ProfilePlotter()
        self._map_viewer = MapViewer()

    def _create_ui(self):
        """建立三欄式 UI 佈局"""
        main_frame = ttk.Frame(self._root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左欄: 輸入面板
        self._input_panel = InputPanel(
            main_frame, on_simulate_callback=self._run_simulation)
        self._input_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # 右欄: 結果面板
        self._result_panel = ResultPanel(main_frame)
        self._result_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # 中欄: 地圖 + 剖面圖
        self._map_panel = MapPanel(main_frame)
        self._map_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _run_simulation(self):
        """執行完整模擬流程"""
        try:
            params = self._input_panel.get_parameters()

            # 地形剖面
            profile = self._terrain_profiler.extract_profile(
                lon1=params['lon1'], lat1=params['lat1'],
                lon2=params['lon2'], lat2=params['lat2'],
                resolution_m=params['resolution_m'])

            # LOS 分析
            los_result = self._los_analyzer.analyze(
                profile, params['h_ant1'], params['h_ant2'])

            # Fresnel 淨空
            fresnel_result = self._fresnel_calc.analyze(profile, los_result)

            # 繞射損耗
            diffraction_result = self._diffraction_calc.calculate(
                profile, los_result, params['h_ant1'], params['h_ant2'])

            # 鏈路預算
            link_result = self._link_budget_calc.received_power(
                tx_power_dbm=params['tx_power_dbm'],
                tx_gain_dbi=params['tx_gain_dbi'],
                rx_gain_dbi=params['rx_gain_dbi'],
                distance_m=profile.total_distance,
                diffraction_loss_db=diffraction_result.total_loss_db)

            # 更新結果
            self._update_results(
                profile, los_result, fresnel_result,
                diffraction_result, link_result)

            # 繪製剖面圖
            self._profile_plotter.plot(
                self._map_panel.fig, profile, los_result,
                fresnel_result, params['h_ant1'], params['h_ant2'])
            self._map_panel.refresh_profile()

            # 更新地圖
            map_html = self._map_viewer.create_map(
                lat1=params['lat1'], lon1=params['lon1'],
                lat2=params['lat2'], lon2=params['lon2'],
                elev1=profile.station1_elevation,
                elev2=profile.station2_elevation,
                is_obstructed=not los_result.is_clear)
            self._map_panel.update_map(map_html)

            self._input_panel.set_status('✅ 模擬完成')

        except ValueError as e:
            messagebox.showerror('輸入錯誤', f'請檢查輸入參數:\n{e}')
            self._input_panel.set_status('❌ 輸入錯誤')
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror('模擬錯誤', f'模擬過程中發生錯誤:\n{e}')
            self._input_panel.set_status('❌ 模擬失敗')

    def _update_results(self, profile, los_result,
                        fresnel_result, diffraction_result, link_result):
        # 計算 Fresnel 最差點的詳細資訊
        i = fresnel_result.min_clearance_index
        worst_los_h = los_result.los_heights[i]
        worst_terrain_h = los_result.terrain_corrected[i]
        worst_clearance = worst_los_h - worst_terrain_h
        worst_fresnel_r = fresnel_result.fresnel_radii[i]
        worst_fresnel_lower = worst_los_h - worst_fresnel_r
        # 侵入深度 = 地形超出 Fresnel 下邊界的量 (正值=侵入, 負值=淨空)
        worst_intrusion = worst_terrain_h - worst_fresnel_lower

        results = {
            'elev1': f'{profile.station1_elevation:.1f}',
            'elev2': f'{profile.station2_elevation:.1f}',
            'distance': f'{profile.total_distance / 1000:.3f}',
            'num_samples': f'{len(profile.distances)}',
            'los_status': '✅ 暢通' if los_result.is_clear else '❌ 遮蔽',
            'max_obstruction': f'{los_result.max_obstruction_height:.1f}',
            'frequency': f'{FREQUENCY_MHZ}',
            'wavelength': f'{WAVELENGTH_M:.4f}',
            'min_clearance': f'{fresnel_result.min_clearance_ratio:.3f}',
            'fresnel_status': '✅ 淨空 (≥0.6)' if fresnel_result.is_clear
                              else '❌ 侵入 (<0.6)',
            # Fresnel 最差點詳情
            'worst_point_dist': f'{profile.distances[i] / 1000:.2f}',
            'worst_los_h': f'{worst_los_h:.1f}',
            'worst_terrain_h': f'{worst_terrain_h:.1f}',
            'worst_clearance': f'{worst_clearance:.1f}',
            'worst_fresnel_r': f'{worst_fresnel_r:.1f}',
            'worst_fresnel_lower': f'{worst_fresnel_lower:.1f}',
            'worst_intrusion': f'{worst_intrusion:.1f}',
            # 損耗
            'fspl': f'{link_result.fspl_db:.2f}',
            'diffraction_loss': f'{diffraction_result.total_loss_db:.2f}',
            'total_loss': f'{link_result.total_path_loss_db:.2f}',
            'rx_power': f'{link_result.rx_power_dbm:.2f}',
        }
        self._result_panel.update_results(results)

    def run(self):
        self._root.mainloop()
