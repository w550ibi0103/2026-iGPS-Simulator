# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, '.')
from config import *
from core.dem_loader import DEMLoader
from core.coordinate import CoordinateConverter
from core.terrain_profile import TerrainProfiler
from core.earth_curvature import EarthCurvature
from core.los_analysis import LOSAnalyzer
from core.fresnel import FresnelCalculator

dem = DEMLoader(DEM_PATH)
conv = CoordinateConverter()
prof = TerrainProfiler(dem, conv)
curve = EarthCurvature()
los_a = LOSAnalyzer(curve)
fres = FresnelCalculator(wavelength=WAVELENGTH_M)

p = prof.extract_profile(120.957259, 23.469984, 120.384587, 23.475295, 20)
lr = los_a.analyze(p, 2, 2)
fr = fres.analyze(p, lr)

i = fr.min_clearance_index
print(f"=== 天線高=2m 分析 ===")
print(f"最差點 index={i}, 距站A={p.distances[i]/1000:.1f} km")
print(f"LOS 高度: {lr.los_heights[i]:.1f} m")
print(f"地形高度(校正後): {lr.terrain_corrected[i]:.1f} m")
print(f"淨空量 (LOS - 地形): {lr.los_heights[i] - lr.terrain_corrected[i]:.1f} m")
print(f"Fresnel 半徑: {fr.fresnel_radii[i]:.1f} m")
print(f"淨空比: {fr.clearance_ratios[i]:.3f}")
print()

# 顯示 fresnel_lower 與地形的關係
fl = fr.fresnel_lower[i]
tc = lr.terrain_corrected[i]
print(f"Fresnel 下邊界: {fl:.1f} m")
print(f"地形 vs Fresnel下邊界差距: {fl - tc:.1f} m")
print(f"  (正值 = 地形在Fresnel下方, 負值 = 地形侵入Fresnel區)")

dem.close()
