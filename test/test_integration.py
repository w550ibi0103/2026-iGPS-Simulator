# -*- coding: utf-8 -*-
"""整合測試 — 驗證修復後的 Deygout 迭代演算法"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEM_PATH, WAVELENGTH_M, FREQUENCY_MHZ
from core.dem_loader import DEMLoader
from core.coordinate import CoordinateConverter
from core.terrain_profile import TerrainProfiler
from core.earth_curvature import EarthCurvature
from core.los_analysis import LOSAnalyzer
from core.fresnel import FresnelCalculator
from core.diffraction import DiffractionCalculator
from core.link_budget import LinkBudgetCalculator

print("=== iGPS 整合測試 ===\n")

dem = DEMLoader(DEM_PATH)
conv = CoordinateConverter()
profiler = TerrainProfiler(dem, conv)
curvature = EarthCurvature()
los = LOSAnalyzer(curvature)
fresnel = FresnelCalculator(wavelength=WAVELENGTH_M)
diffraction = DiffractionCalculator(wavelength=WAVELENGTH_M)
link = LinkBudgetCalculator(frequency_mhz=FREQUENCY_MHZ)

# 測試: 使用者回報的座標 (原本會造成 recursion depth exceeded)
print("--- 測試: 墾丁→蘭嶼方向 (原 bug 座標) ---")
profile = profiler.extract_profile(
    120.89730, 22.10473, 121.50418, 22.08187, resolution_m=20)
print(f"距離: {profile.total_distance/1000:.1f} km")
print(f"取樣點數: {len(profile.distances)}")
print(f"站A海拔: {profile.station1_elevation:.1f} m")
print(f"站B海拔: {profile.station2_elevation:.1f} m")

los_r = los.analyze(profile, 2, 2)
print(f"LOS 暢通: {los_r.is_clear}")
print(f"遮蔽點數: {len(los_r.obstruction_indices)}")
print(f"最大遮蔽高度: {los_r.max_obstruction_height:.1f} m")

fresnel_r = fresnel.analyze(profile, los_r)
print(f"最小淨空比: {fresnel_r.min_clearance_ratio:.3f}")

diff_r = diffraction.calculate(profile, los_r, 2, 2)
print(f"繞射損耗: {diff_r.total_loss_db:.2f} dB")

link_r = link.received_power(10, 2, 2, profile.total_distance, diff_r.total_loss_db)
print(f"FSPL: {link_r.fspl_db:.2f} dB")
print(f"接收功率: {link_r.rx_power_dbm:.2f} dBm")

dem.close()
print("\n=== 測試完成 (無 recursion error) ===")
