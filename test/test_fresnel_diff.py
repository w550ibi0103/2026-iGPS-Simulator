import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEM_PATH, WAVELENGTH_M
from core.dem_loader import DEMLoader
from core.coordinate import CoordinateConverter
from core.terrain_profile import TerrainProfiler
from core.earth_curvature import EarthCurvature
from core.los_analysis import LOSAnalyzer
from core.fresnel import FresnelCalculator

print("=== Fresnel Calculation Bug Tester ===")

dem = DEMLoader(DEM_PATH)
conv = CoordinateConverter()
profiler = TerrainProfiler(dem, conv)
curvature = EarthCurvature()
los = LOSAnalyzer(curvature)
fresnel_new = FresnelCalculator(wavelength=WAVELENGTH_M)

lon1, lat1 = 120.879030, 22.322570
lon2, lat2 = 121.50418, 22.08187

# Let's test Old Fresnel Mock with curvature = 0, +, -
class OldFresnelMock:
    def __init__(self, dem, conv, wavelength):
        self._dem = dem
        self._conv = conv
        self._wavelength = wavelength
        self._R_eff = 6371000 * (4/3)

    def interpolate_height(self, x, y):
        return self._dem.get_elevation(x, y)

    def get_shape(self):
        return (self._dem._height, self._dem._width)

    def fresnel_clearance(self, tx1_twd97_xyz: list, tx2_twd97_xyz: list, curve_sign=1):
        tx1_twd97_xyz_np = np.array(tx1_twd97_xyz)
        tx2_twd97_xyz_np = np.array(tx2_twd97_xyz)

        r_squared = (tx1_twd97_xyz_np[0] - tx2_twd97_xyz_np[0]) ** 2 + (tx1_twd97_xyz_np[1] - tx2_twd97_xyz_np[1]) ** 2 + (tx1_twd97_xyz_np[2] - tx2_twd97_xyz_np[2]) ** 2
        r = r_squared ** 0.5
        n_samples = int(r / 20)
        total_dist = np.linalg.norm(tx2_twd97_xyz_np[:2] - tx1_twd97_xyz_np[:2])

        worst_margin = np.inf
        ts = np.linspace(0, 1, n_samples)
        
        self._dem_ds = self

        for t in ts:
            d1 = t * total_dist
            d2 = (1 - t) * total_dist

            if d1 == 0 or d2 == 0:  
                continue
            else:
                fresnel_r = np.sqrt(self._wavelength * d1 * d2 / (d1 + d2))

                twd97_x = tx1_twd97_xyz_np[0] + t * (tx2_twd97_xyz_np[0] - tx1_twd97_xyz_np[0])
                twd97_y = tx1_twd97_xyz_np[1] + t * (tx2_twd97_xyz_np[1] - tx1_twd97_xyz_np[1])
                z_line = tx1_twd97_xyz_np[2] + t * (tx2_twd97_xyz_np[2] - tx1_twd97_xyz_np[2])

                h_curvature = curve_sign * (d1 * d2 / (2 * self._R_eff))

                try:
                    import rasterio.transform
                    row, col = rasterio.transform.rowcol(self._dem.get_transform(), twd97_x, twd97_y)
                except:
                    row, col = -1, -1

                if row < 0 or col < 0 or row >= self._dem_ds.get_shape()[0] or col >= self._dem_ds.get_shape()[1]:
                    continue
                else:
                    z_terrain = self.interpolate_height(twd97_x, twd97_y) + h_curvature
                    clearance = z_line - z_terrain

                    margin = clearance / fresnel_r
                    worst_margin = min(worst_margin, margin)

        return worst_margin

x1, y1 = conv.wgs84_to_twd97(lon1, lat1)
x2, y2 = conv.wgs84_to_twd97(lon2, lat2)
z1 = dem.get_elevation(x1, y1)
z2 = dem.get_elevation(x2, y2)

old_calc = OldFresnelMock(dem, conv, WAVELENGTH_M)

for h in range(1, 16):
    margin = old_calc.fresnel_clearance([x1, y1, z1 + h], [x2, y2, z2 + h], curve_sign=1)
    margin_no_curve = old_calc.fresnel_clearance([x1, y1, z1 + h], [x2, y2, z2 + h], curve_sign=0)
    margin_neg_curve = old_calc.fresnel_clearance([x1, y1, z1 + h], [x2, y2, z2 + h], curve_sign=-1)
    
    if abs(margin - 0.74) < 0.02 or abs(margin_no_curve - 0.74) < 0.02 or abs(margin_neg_curve - 0.74) < 0.02:
        print(f"h_ant={h}m => normal: {margin:.3f}, no_curve: {margin_no_curve:.3f}, neg_curve: {margin_neg_curve:.3f}")

print("\n=== Test Finished ===")
dem.close()
