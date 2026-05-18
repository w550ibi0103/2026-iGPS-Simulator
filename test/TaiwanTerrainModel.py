import rasterio
import numpy as np
from pyproj import Transformer
import pyvista as pv
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class TaiwanTerrainModel:
    def __init__(self) -> None:
        try:
            self._tif_path = None
            self._dem = None
            self._transform = None
            self._dem_ds = None
            self._downsampling_step = 1
            self._llh_to_twd97 = Transformer.from_crs("EPSG:4326", "EPSG:3826", always_xy=True)  # EPSG:4326 = WGS84 lat/lon, EPSG:3826 = TWD97 TM2 (121)
            self._frequency = 377.5e6
            self._wavelength = 299792000 / self._frequency  # speed of light in vacuum = 299,792,458, speed of light in the air = 299,792,000
            self._R_eff = 4/3 * 6371000  # R_eff = k * Re
            # x_dist = t * total_dist
            # h_curv = x_dist * (total_dist - x_dist) / (2 * R_eff)
            self.X = None
            self.Y = None
            self.Z = None
        except Exception as e:
            print(f"[TaiwanTerrainModel] [init] An error occurred while initializing: {e}")
            raise
    
    def open(self, tif_path: str) -> None:
        self._tif_path = tif_path
        with rasterio.open(self._tif_path) as src:
            self._dem = src.read(1)  # 只有 1 個 band, 返回 numpy.ndarray
            self._dem_ds = self._dem
            self._transform = src.transform  # 從影像像素座標 (row, col) → 真實世界座標 (X, Y) 的數學轉換的 matrix
            print(f"[TaiwanTerrainModel] [open] An tif file is opened.")
    
    def downsampling(self, downsampling_step: int) -> np.ndarray:
        self._downsampling_step = downsampling_step
        self._dem_ds = self._dem[::self._downsampling_step, ::self._downsampling_step]
        print(f"[TaiwanTerrainModel] [downsampling] Downsample is finished.")
    
    def plot_twd97_pv(self):
        nrows, ncols = self._dem_ds.shape  # 輸出 = (行數, 列數)
        x_coords = np.arange(ncols) * self._transform.a * self._downsampling_step + self._transform.c  # a = pixel width, c = x_origin
        y_coords = np.arange(nrows) * self._transform.e * self._downsampling_step + self._transform.f  # e = pixel height, f = y_origin
        self.X, self.Y = np.meshgrid(x_coords, y_coords, indexing='xy')  # 輸入: 接收一維座標陣列 x 和 y, 輸出: 返回兩個二維陣列 X, Y, X 每一列都一樣, Y 每一欄都一樣
        self.Z = self._dem_ds
        grid = pv.StructuredGrid(self.X, self.Y, self.Z)
        plotter = pv.Plotter()
        plotter.add_mesh(grid, cmap="terrain")
        plotter.add_axes()
        plotter.add_scalar_bar(title="Elevation (m)")
        plotter.show(title="Taiwan DEM (20m)")
        print(self.Z[0, 0])
        print("Grid dimensions (nx, ny, nz):", grid.dimensions)
    
    def plot_twd97_mpl(self):
        # 1. 取得數據
        nrows, ncols = self._dem_ds.shape
        x_coords = np.arange(ncols) * self._transform.a * self._downsampling_step + self._transform.c
        y_coords = np.arange(nrows) * self._transform.e * self._downsampling_step + self._transform.f
        
        X, Y = np.meshgrid(x_coords, y_coords)
        Z = self._dem_ds.copy().astype(float) # 轉成 float 以支援 nan 或 mask

        # 2. 處理海平面與 NoData (-32767)
        # 我們只保留 Z > 0 的部分，其餘遮蔽
        Z_masked = np.ma.masked_where(Z <= 0, Z)

        # 3. 繪圖
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        # 使用遮罩後的 Z_masked
        surf = ax.plot_surface(X, Y, Z_masked, 
                            cmap='terrain', 
                            rcount=300, ccount=300,
                            linewidth=0, 
                            antialiased=True,
                            shade=True)

        # 4. 優化視覺效果：設定 Z 軸範圍
        # 這樣座標軸就不會被 -32767 拉走
        ax.set_zlim(0, np.max(Z_masked) + 100)

        # 5. 調整標籤
        ax.set_title("Taiwan Topography (Land Only)")
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=15)
        
        # 讓地形比例好看一點（x, y 很大，z 很小，所以通常會加強 z 軸）
        ax.set_box_aspect((1, 1, 0.1)) 

        plt.show()

    def llh_to_twd97_xyz(self, lon: float, lat: float, height_compensation: float) -> list:
        # 1. lat/lon → TWD97
        twd97_x, twd97_y = self._llh_to_twd97.transform(lon, lat)

        # 2. TWD97 → DEM pixel
        row, col = self.twd97_xy_to_pixel(twd97_x, twd97_y)

        # 3. 邊界檢查
        if row < 0 or col < 0 or row >= self._dem_ds.shape[0] or col >= self._dem_ds.shape[1]:
            raise ValueError("Point outside DEM.")
        else:
            z = self.interpolate_height(twd97_x, twd97_y) + height_compensation
            print(f"[TaiwanTerrainModel] [llh_to_twd97_xyz] TWD97 coordinate is {twd97_x:.5f}, {twd97_y:.5f}, {z:.5f}.")
            return [twd97_x, twd97_y, z]

    def twd97_xy_to_pixel(self, twd97_x: float, twd97_y: float) -> tuple:
        col = (twd97_x - self._transform.c) / (self._transform.a * self._downsampling_step)
        row = (twd97_y - self._transform.f) / (self._transform.e * self._downsampling_step)
        return row, col

    def interpolate_height(self, twd97_x: float, twd97_y: float) -> float:
        row, col = self.twd97_xy_to_pixel(twd97_x, twd97_y)

        r0 = int(np.floor(row))  # 對輸入 row 取向下取整（floor）, 也就是把小數部分去掉
        c0 = int(np.floor(col))
        r1 = r0 + 1
        c1 = c0 + 1

        if (r0 < 0 or c0 < 0 or r1 >= self._dem_ds.shape[0] or c1 >= self._dem_ds.shape[1]):
            return np.nan
        else:
            z00 = self._dem_ds[r0, c0]
            z10 = self._dem_ds[r1, c0]
            z01 = self._dem_ds[r0, c1]
            z11 = self._dem_ds[r1, c1]

            # 將 -32767 轉換成 0
            NODATA = -32767.0
            if z00 == NODATA:
                z00 = 0.0
            if z10 == NODATA:
                z10 = 0.0
            if z01 == NODATA:
                z01 = 0.0
            if z11 == NODATA:
                z11 = 0.0

            dr = row - r0
            dc = col - c0

            z0 = z00 * (1 - dc) + z01 * dc
            z1 = z10 * (1 - dc) + z11 * dc
            z = z0 * (1 - dr) + z1 * dr

            return z

    def check_los(self, tx1_twd97_xyz: list, tx2_twd97_xyz: list) -> bool:  # Line-of-Sight
        tx1_twd97_xyz_np = np.array(tx1_twd97_xyz)
        tx2_twd97_xyz_np = np.array(tx2_twd97_xyz)

        r_squared = (tx1_twd97_xyz_np[0] - tx2_twd97_xyz_np[0]) ** 2 + (tx1_twd97_xyz_np[1] - tx2_twd97_xyz_np[1]) ** 2 + (tx1_twd97_xyz_np[2] - tx2_twd97_xyz_np[2]) ** 2
        r = r_squared ** 0.5
        n_samples = int(r / 20)
        print(f"[TaiwanTerrainModel] [check_los] Number of line samples is {n_samples}.")

        total_dist = np.linalg.norm(tx2_twd97_xyz_np[:2] - tx1_twd97_xyz_np[:2])

        # 直線參數 t ∈ [0,1]
        ts = np.linspace(0, 1, n_samples)

        for t in ts:
            d1 = t * total_dist
            d2 = (1 - t) * total_dist

            if d1 == 0 or d2 == 0:  # 不要對端點套用 fresnel / diffraction 模型
                continue
            else:
                twd97_x = tx1_twd97_xyz_np[0] + t * (tx2_twd97_xyz_np[0] - tx1_twd97_xyz_np[0])
                twd97_y = tx1_twd97_xyz_np[1] + t * (tx2_twd97_xyz_np[1] - tx1_twd97_xyz_np[1])
                z_line = tx1_twd97_xyz_np[2] + t * (tx2_twd97_xyz_np[2] - tx1_twd97_xyz_np[2])

                # Earth curvature
                h_curvature = d1 * d2 / (2 * self._R_eff)

                # 對應 DEM
                row, col = self.twd97_xy_to_pixel(twd97_x, twd97_y)

                if row < 0 or col < 0 or row >= self._dem_ds.shape[0] or col >= self._dem_ds.shape[1]:
                    continue
                else:
                    z_terrain = self.interpolate_height(twd97_x, twd97_y) + h_curvature

                    if z_terrain > z_line:
                        print(f"[TaiwanTerrainModel] [check_los] Z line is blocked by terrain.")
                        return False  # 被遮蔽

        print(f"[TaiwanTerrainModel] [check_los] Z line is cleared.")
        return True  # LOS

    def fresnel_clearance(self, tx1_twd97_xyz: list, tx2_twd97_xyz: list):
        tx1_twd97_xyz_np = np.array(tx1_twd97_xyz)
        tx2_twd97_xyz_np = np.array(tx2_twd97_xyz)

        r_squared = (tx1_twd97_xyz_np[0] - tx2_twd97_xyz_np[0]) ** 2 + (tx1_twd97_xyz_np[1] - tx2_twd97_xyz_np[1]) ** 2 + (tx1_twd97_xyz_np[2] - tx2_twd97_xyz_np[2]) ** 2
        r = r_squared ** 0.5
        n_samples = int(r / 20)
        print(f"[TaiwanTerrainModel] [fresnel_clearance] Number of line samples is {n_samples}.")

        total_dist = np.linalg.norm(tx2_twd97_xyz_np[:2] - tx1_twd97_xyz_np[:2])

        worst_margin = np.inf

        ts = np.linspace(0, 1, n_samples)

        for t in ts:
            d1 = t * total_dist
            d2 = (1 - t) * total_dist

            if d1 == 0 or d2 == 0:  # 不要對端點套用 fresnel / diffraction 模型
                continue
            else:
                fresnel_r = np.sqrt(self._wavelength * d1 * d2 / (d1 + d2))

                twd97_x = tx1_twd97_xyz_np[0] + t * (tx2_twd97_xyz_np[0] - tx1_twd97_xyz_np[0])
                twd97_y = tx1_twd97_xyz_np[1] + t * (tx2_twd97_xyz_np[1] - tx1_twd97_xyz_np[1])
                z_line = tx1_twd97_xyz_np[2] + t * (tx2_twd97_xyz_np[2] - tx1_twd97_xyz_np[2])

                # Earth curvature
                h_curvature = d1 * d2 / (2 * self._R_eff)

                row, col = self.twd97_xy_to_pixel(twd97_x, twd97_y)

                if row < 0 or col < 0 or row >= self._dem_ds.shape[0] or col >= self._dem_ds.shape[1]:
                    continue
                else:
                    z_terrain = self.interpolate_height(twd97_x, twd97_y) + h_curvature
                    clearance = z_line - z_terrain

                    margin = clearance / fresnel_r
                    worst_margin = min(worst_margin, margin)

        print(f"[TaiwanTerrainModel] [fresnel_clearance] Fresnel clearance is {worst_margin:.2f}.")
        return worst_margin  # >0.6 為良好

    # tx1_gain_dbi 為發射天線增益, tx2_gain_dbi 為接收天線增益, fspl 為自由空間損耗, diff_loss 為繞射損耗, misc_loss_db 為其他損耗
    # 其他損耗可能為 cable loss, connector loss, polarization mismatch, atmospheric absorption, rain fade
    def received_power_dbm(self, tx1_twd97_xyz, tx2_twd97_xyz, tx1_power_dbm=0, tx1_gain_dbi=0, tx2_gain_dbi=0, misc_loss_db=0):  # ZHL-50W-52-S+ gain is 47 ~ 52db, but output P1db = 44 ~ 46.5 dbm, output P3db = 45.5 ~ 48 dbm
        total_dist = np.linalg.norm(np.array(tx2_twd97_xyz[:2]) - np.array(tx1_twd97_xyz[:2]))  # tx antenna gain is 6.8 dbi, rx antenna gain is 2.15 dbi

        fspl = self.fspl_db(total_dist)
        diff_loss = self.diffraction_loss_from_profile(tx1_twd97_xyz, tx2_twd97_xyz)

        prx = (tx1_power_dbm + tx1_gain_dbi + tx2_gain_dbi - fspl - diff_loss - misc_loss_db)
        print(f"[TaiwanTerrainModel] [received_power_dbm] Receive power is {prx:.2f} dbm, fspl is {fspl:.2f} dbm, diffraction loss is {diff_loss:.2f} db, distance is {total_dist:.2f} meters.")

        return prx
    
    def fspl_db(self, distance_m):  # free space path loss
        distance_km = distance_m / 1000
        frequency_mhz = self._frequency / 1e6
        return 20 * np.log10(distance_km) + 20 * np.log10(frequency_mhz) + 32.44

    def knife_edge_loss_from_profile(self, tx1_twd97_xyz: list, tx2_twd97_xyz: list):
        tx1_twd97_xyz_np = np.array(tx1_twd97_xyz)
        tx2_twd97_xyz_np = np.array(tx2_twd97_xyz)

        r_squared = (tx1_twd97_xyz_np[0] - tx2_twd97_xyz_np[0]) ** 2 + (tx1_twd97_xyz_np[1] - tx2_twd97_xyz_np[1]) ** 2 + (tx1_twd97_xyz_np[2] - tx2_twd97_xyz_np[2]) ** 2
        r = r_squared ** 0.5
        n_samples = int(r / 20)
        print(f"[TaiwanTerrainModel] [knife_edge_loss_from_profile] Number of line samples is {n_samples}.")

        total_dist = np.linalg.norm(tx2_twd97_xyz_np[:2] - tx1_twd97_xyz_np[:2])

        max_h = -np.inf
        max_t = None

        ts = np.linspace(0, 1, n_samples)

        for t in ts:
            d1 = t * total_dist
            d2 = (1 - t) * total_dist

            if d1 == 0 or d2 == 0:  # 不要對端點套用 fresnel / diffraction 模型
                continue
            else:
                twd97_x = tx1_twd97_xyz_np[0] + t * (tx2_twd97_xyz_np[0] - tx1_twd97_xyz_np[0])
                twd97_y = tx1_twd97_xyz_np[1] + t * (tx2_twd97_xyz_np[1] - tx1_twd97_xyz_np[1])
                z_line = tx1_twd97_xyz_np[2] + t * (tx2_twd97_xyz_np[2] - tx1_twd97_xyz_np[2])

                # Earth curvature
                h_curvature = d1 * d2 / (2 * self._R_eff)

                z_terrain = self.interpolate_height(twd97_x, twd97_y) + h_curvature
    
                if np.isnan(z_terrain):
                    continue
                else:
                    h = z_terrain - z_line  # 找出遮蔽最嚴重的 h, 也就是地形扣掉 z line 的距離最大的地方
                    # print(f"[TaiwanTerrainModel] [knife_edge_loss_from_profile] h is {h:.2f}, z_terrain is {z_terrain:.2f}, z_line is {z_line:.2f}.")
                    if h > max_h:
                        max_h = h
                        max_t = t
        if max_h <= 0:
            print(f"[TaiwanTerrainModel] [knife_edge_loss_from_profile] Max height is {max_h:.2f} meters above terrain.")
            return 0.0  # LOS clear
        else:
            d1 = max_t * total_dist
            d2 = (1 - max_t) * total_dist
            edge_loss = self.knife_edge_loss(max_h, d1, d2)
            print(f"[TaiwanTerrainModel] [knife_edge_loss_from_profile] Max height is {max_h:.2f} meters below terrain, distance_1 is {d1:.2f} meters, distance_2 is {d2:.2f} meters, knife edge loss is {edge_loss:.2f} db.")
            return edge_loss

    def diffraction_loss_from_profile(self, tx1_twd97_xyz: list, tx2_twd97_xyz: list, n_samples=500, k_factor=4/3):
        tx1_twd97_xyz_np = np.array(tx1_twd97_xyz)
        tx2_twd97_xyz_np = np.array(tx2_twd97_xyz)

        r_squared = (tx1_twd97_xyz_np[0] - tx2_twd97_xyz_np[0]) ** 2 + (tx1_twd97_xyz_np[1] - tx2_twd97_xyz_np[1]) ** 2 + (tx1_twd97_xyz_np[2] - tx2_twd97_xyz_np[2]) ** 2
        r = r_squared ** 0.5
        n_samples = int(r / 20)
        print(f"[TaiwanTerrainModel] [diffraction_loss_from_profile] Number of line samples is {n_samples}.")

        total_dist = np.linalg.norm(tx2_twd97_xyz_np[:2] - tx1_twd97_xyz_np[:2])

        max_h = -np.inf
        max_d1 = None
        max_d2 = None

        ts = np.linspace(0, 1, n_samples)

        for t in ts:
            d1 = t * total_dist
            d2 = (1 - t) * total_dist

            if d1 == 0 or d2 == 0:  # 不要對端點套用 fresnel / diffraction 模型
                continue
            else:
                # LOS height
                twd97_x = tx1_twd97_xyz_np[0] + t * (tx2_twd97_xyz_np[0] - tx1_twd97_xyz_np[0])
                twd97_y = tx1_twd97_xyz_np[1] + t * (tx2_twd97_xyz_np[1] - tx1_twd97_xyz_np[1])
                z_line = tx1_twd97_xyz_np[2] + t * (tx2_twd97_xyz_np[2] - tx1_twd97_xyz_np[2])

                # Earth curvature
                h_curvature = d1 * d2 / (2 * self._R_eff)

                z_terrain = self.interpolate_height(twd97_x, twd97_y) + h_curvature

                if np.isnan(z_terrain):
                    continue
                else:
                    # Fresnel radius
                    r1 = np.sqrt(self._wavelength * d1 * d2 / (d1 + d2))

                    # Effective obstruction height
                    h = z_terrain - (z_line - r1)  # 原本的 z line 加上 Fresnel radius 的範圍, 也就是地形扣掉 z line - r1 的距離最大的地方

                    if h > max_h:
                        max_h = h
                        max_d1 = d1
                        max_d2 = d2
        if max_h <= 0:
            print(f"[TaiwanTerrainModel] [diffraction_loss_from_profile] Max height is {max_h:.2f} meters above terrain.")
            return 0.0
        else:
            diffraction_loss = self.knife_edge_loss(max_h, max_d1, max_d2)
            print(f"[TaiwanTerrainModel] [diffraction_loss_from_profile] Max height is {max_h:.2f} meters below terrain, distance_1 is {max_d1:.2f} meters, distance_2 is {max_d2:.2f} meters, diffraction edge loss is {diffraction_loss:.2f} db.")
            return diffraction_loss

    def knife_edge_loss(self, h, d1, d2):
        v = h * np.sqrt(2 * (d1 + d2) / (self._wavelength * d1 * d2))

        if v <= -0.7:  # ν < −0.7 → 幾乎無損耗
            return 0.0
        else:  # −0.7 < ν < 0 → 有少量損耗, ν > 0 → 明顯繞射
            return 6.9 + 20 * np.log10(np.sqrt((v - 0.1)**2 + 1) + v - 0.1)

    # N = KTB, 熱雜訊功率
    # N0 = kT (w/Hz) = N / B, N0 為溫度 290K (17°C) 的電阻產生的雜訊功率譜密度
    # N0 (dbm/Hz) = 10 * log10(kT) = 10 * log10(1.38*10^-23 * 290) = -203.98 dbw/Hz = -174 dbm/Hz (每 1 Hz 頻寬內的雜訊功率)
    # Pn (dbm) = 總雜訊功率 = 10 * log10(KTB) + noise figure = N0 + 10 * log10(B) + noise figure = -174 + 10 * log10(bandwidth) + noise figure (接收器自己產生的雜訊)
    # N0 單位是 dbm/Hz, 10 * log10(B) 單位是 db, B 的單位其實是「對 1 Hz 的比例」, 也就是 10 * log10​(B/1Hz)
    # noise floor (平均雜訊位準) = -174 + 10 * log10(RBW) + noise figure
    # RBW = sample rate / n of FFT, 增加 10 倍點數, RBW 變成 1/10, noise floor 會降 10 dB
    # USRP 的 noise floor = -174 + 10 * log(10M) + 7 = -97 dbm
    def noise_floor_dbm(self, bandwidth_hz, noise_figure_db):  # USRP-2950R 的 noise figure (RX) 為 5 dB to 7 dB
        noise_floor = -174 + 10 * np.log10(bandwidth_hz) + noise_figure_db
        return noise_floor
    
    # SNR = signal power / noise power = Psignal / Pnoise 
    # SNR (db) = 10 * log10(signal power / noise power) = 10 * log10(Prx / N0B) = Prx (dbm) - noise floor (dbm), 展頻後 B 變大, SNR 變差, 但不代表真的變差
    # Gp (db) = 10 * log10(B / Rb), Gp 為 processing Gain = 處理增益, B 為展頻後的頻寬 or chip rate, Rb 為原始數據傳輸率
    # 如果訊號在空氣中比雜訊低 15 dB (SNR_raw = -15dB), 但你的處理增益有 20 dB, 解展頻後你的訊號就會變為 +5 dB, 足以被正確解碼
    # 展頻的 SNR (db) = SNR_raw + Gp, SNR_raw = 10 * log10(signal power / noise power) + 10 * log10(B / Rb)
    # 展頻的 SNR = (signal power / noise power) * (B / Rb) = (Prx / N0B) * (B / Rb) = Prx / (N0 * Rb)
    # Eb = Prx / Rb = 每位元能量
    # 展頻的 SNR = Prx / (N0 * Rb) = Eb / N0, Eb / N0 為每位元能量對雜訊功率譜密度比
    # 這裡的 snr 是 snr_raw, 也就是「空氣中」的 SNR
    # iGPS 的例子中, prx_dbm 只能用算的, noise_floor_dbm = -97 dbm, 展頻的 prx_dbm 通常比 noise_floor_dbm 小, 因此 snr_db 是負的
    def snr_db(self, prx_dbm, noise_floor_dbm):
        return prx_dbm - noise_floor_dbm

    # log2(x) = ln(x) / ln(2)
    # C = B * log2(1 + SNR) = B * ln(1 + SNR) / ln(2)
    # 當 SNR 很小時, ln(1 + SNR) = SNR
    # C = B * SNR / ln(2) = 1.44B * SNR
    # 假設 SNR = -50 db = 0.00001, C = B * log2(1 + SNR) = 10M * log2(1 + 0.00001) = 144.269
    # 在 10MHz 的頻寬裡, 如果雜訊比訊號強 50dB, 這條物理通道理論上最高可以跑 144bps, 實際上只跑了 100bps
    # 假設 SNR = -34 db = 0.000398107, C = B * log2(1 + SNR) = 2.5M * log2(1 + 0.000398107) = 1435.582
    # 在 2.5MHz 的頻寬裡, 如果雜訊比訊號強 34dB, 這條物理通道理論上最高可以跑 1435bps, 實際上只跑了 100bps
    # 假設 SNR = -50 db = 0.00001, C = B * log2(1 + SNR) = 2.5M * log2(1 + 0.00001) = 36.067
    # 在 2.5MHz 的頻寬裡, 如果雜訊比訊號強 50dB, 這條物理通道理論上最高可以跑 36bps, 實際上跑了 100bps, 無法傳輸
    def shannon_capacity(self, bandwidth_hz, snr_db):  # C = B * log2(1 + SNR), 在這個頻寬與雜訊下, 任何調變方式都不可能超過這個速率
        snr_linear = 10 ** (snr_db / 10)  # 把 db 轉回倍率
        return bandwidth_hz * np.log2(1 + snr_linear)
        
    # data rate = bandwidth * bits/symbol * coding rate. coding rate 是編碼率, 為了抗雜訊, 故意多送一些「冗餘位元」, 來做 FEC（Forward Error Correction）
    # bit per symbol = log2(M), 為 1 個 symbol 能承載幾個 bit, M 為可能 symbol 數. 如 QPSK 有 4 個 symbols, M = 4, 每個 symbol 有 log2(4) = 2 bits.
    # 在展頻系統中, 有效頻寬 = 傳輸頻寬 (Rc) / 擴散因子 (SF), 因此有效頻寬 = 10M / 100k = 100 Hz
    # 擴散因子 (SF) = samples per symbol * symbols per bit = 10k * 10 = 100k
    # 在 iGPS 展頻系統中, 有效頻寬 = 傳輸頻寬 (Rc) / 擴散因子 (SF), 因此 iGPS 的有效頻寬 = 2.5M / 25k = 100 Hz
    # 擴散因子 (SF) = samples per symbol * symbols per bit = 2.5k * 10 = 25k
    # data rate = 100 * 1 * 1/2 = 50 bps
    def data_rate(self, bandwidth_hz, bit_per_symbol, code_rate):
        return bandwidth_hz * bit_per_symbol * code_rate

    # iq rate = 10M/s
    # 原始 prn = 2500 chips
    # 實際應用 prn = 2500 * 4 = 10k chips = 10k samples = 1ms
    # chip rate (Rc) = 10M chips per seconds = 10M/s
    # bandwidth = chip rate
    # 10k chips = 1 symbol = 1ms
    # symbol rate (Rs) = 1k symbols/s
    # 1 bit = 10 symbols = 10ms
    # bit rate (Rb) = 100bps = data rate
    # net bit rate = 100bps * code rate = 100bps * (300/600) = 50bps
    # B 指的是「展頻後的頻寬」, 訊號因為是由 10M 的 Chip Rate 組成的，所以它在頻譜上佔用的頻寬 B = 10MHz
    # B / Rb = 10M / 100 = 100k
    # 擴散比 (Spreading Ratio) = 10M / 100 = 100k 倍, 把一個 100 bps 的極窄訊號, 散布到了 10MHz 的廣大頻譜空間裡
    # Gp1 (db) = 10 * log10(B / Rs) = 10 * log10(10M / 1k) = 40 db, 在頻譜儀或相關運算後, 你會看到訊號從雜訊中「拔地而起」 40 dB, 這時你得到的是一個個的 Symbols
    # Gp (db) = 10 * log10(B / Rb) = 10 * log(10M / 100) = 50 db, 剩下的 10 dB 是透過「累積 10 個 Symbol 的能量」來換取的
    # 在算 Gp (處理增益) 時, 分母先帶 100bps, 因為這才是實體層展頻碼所對應的資料寬度
    # 展頻的 SNR (db) = SNR_raw + Gp = 10 * log10(signal power / noise power) + 10 * log10(B / Rb)
    # 假設 SNR_raw = -50 db = 0.00001
    # Eb / N0 (db) = -50 + 10 * log(10M / 100) = -50 + 10 * log(100k) = 0
    # 對於 BPSK 調變, 通常只要 Eb/N0 > 10dB, 誤碼率就幾乎可以降到 10^-5 以下
    # 比較保險是 SNR_raw = -40 db = 0.0001, 也就是比 noise_floor_dbm 小 40db = -97dbm - 40 = -137dbm

    # iq rate = 10M/s
    # 原始 prn = 2500 chips
    # 實際應用 prn = 2500 * 4 = 10k chips = 10k samples = 1ms
    # 等效於 prn = 2500 = 2.5k samples = 1ms @ iq rate = 2.5M/s
    # 雖然有 10000 個點, 但因為每 4 個點才跳變一次, 你的實際切換速度（Chip Rate）降到了 2.5M/s
    # chip rate (Rc) = 2.5M chips per seconds = 2.5M/s
    # bandwidth = chip rate
    # 2.5k chips = 1 symbol = 1ms
    # symbol rate (Rs) = 1k symbols/s
    # 1 bit = 10 symbols = 10ms
    # bit rate (Rb) = 100bps = data rate
    # net bit rate = 100bps * code rate = 100bps * (300/600) = 50bps
    # B 指的是「展頻後的頻寬」, 訊號因為是由 2.5M 的 Chip Rate 組成的，所以它在頻譜上佔用的頻寬 B = 2.5MHz
    # B / Rb = 2.5M / 100 = 25k
    # 擴散比 (Spreading Ratio) = 2.5M / 100 = 25k 倍, 把一個 100 bps 的極窄訊號, 散布到了 2.5MHz 的廣大頻譜空間裡
    # Gp1 (db) = 10 * log10(B / Rs) = 10 * log10(2.5M / 1k) = 34 db, 在頻譜儀或相關運算後, 你會看到訊號從雜訊中「拔地而起」 34 dB, 這時你得到的是一個個的 Symbols
    # Gp (db) = 10 * log10(B / Rb) = 10 * log(2.5M / 100) = 44 db, 剩下的 10 dB 是透過「累積 10 個 Symbol 的能量」來換取的
    # 在算 Gp (處理增益) 時, 分母先帶 100bps, 因為這才是實體層展頻碼所對應的資料寬度
    # 展頻的 SNR (db) = SNR_raw + Gp = 10 * log10(signal power / noise power) + 10 * log10(B / Rb)
    # 假設 SNR_raw = -34 db = 0.00039811
    # Eb / N0 (db) = -34 + 10 * log(2.5M / 100) = -34 + 10 * log(25k) = -34 + 44 = 10
    # 對於 BPSK 調變, 通常只要 Eb/N0 > 10dB, 誤碼率就幾乎可以降到 10^-5 以下
    # 比較保險是 SNR_raw = -34 db = 0.00039811, 也就是比 noise_floor_dbm 小 34db = -97dbm - 34 = -131dbm
    # 如果是看 correlation 圖, 必須要看到有訊號的話, Gp1 (db) = 10 * log10(B / Rs) = 10 * log10(2.5M / 1k) = 34 db, 因此比較保險是 SNR_raw = -24 db, 也就是比 noise_floor_dbm 小 24db = -97dbm - 24 = -121dbm

    def eb_n0_db(snr_rf_db, bandwidth_hz, bit_rate):
        return snr_rf_db + 10*np.log10(bandwidth_hz / bit_rate)

if __name__ == "__main__":
    # r"C:\Users\genui\Downloads\Taiwan_DEM\不分幅_全台20MDEM(2024)\不分幅_台灣20MDEM(2024).tif"
    tif_path = r"C:\Users\genui\Downloads\Taiwan_DEM\不分幅_全台20MDEM(2025)\DEM_tawiwan_V2025.tif"
    twterrain = TaiwanTerrainModel()

    # 打開 tif
    twterrain.open(tif_path)

    # 降取樣畫圖才不會吃太多資源, pv 降取樣 10, mpl 降取樣 100
    # twterrain.downsampling(10)
    # twterrain.plot_twd97_pv()
    # twterrain.plot_twd97_mpl()

    # 各站座標帶入模型
    dawu_fishing_port = twterrain.llh_to_twd97_xyz(120.897111, 22.337290, 0)  # tx1 附近無遮蔽的平地
    tx1_wangyou_pavilion = twterrain.llh_to_twd97_xyz(120.879030, 22.322570, 2)
    tx2_xuhai_grassland = twterrain.llh_to_twd97_xyz(120.88529, 22.20458,5)
    tx3_building_045 = twterrain.llh_to_twd97_xyz(120.88943, 22.14172, 2)
    tx4_nanrenbi = twterrain.llh_to_twd97_xyz(120.89730, 22.10473, 5)
    tx5_lanyu = twterrain.llh_to_twd97_xyz(121.50418, 22.08187, 2)
    rx_chiupeng_sea = twterrain.llh_to_twd97_xyz(121.02370, 22.15788, 2)
    yushan = twterrain.llh_to_twd97_xyz(120.957259, 23.469984, 0)
    chayi_cha64 = twterrain.llh_to_twd97_xyz(120.384587, 23.475295, 0)

    # 計算 los, fresnel clearance, 地形 loss, received power
    los_result = twterrain.check_los(tx1_wangyou_pavilion, tx5_lanyu)
    fresnel_clearance_result = twterrain.fresnel_clearance(tx1_wangyou_pavilion, tx5_lanyu)
    knife_edge_loss_result = twterrain.knife_edge_loss_from_profile(tx1_wangyou_pavilion, tx5_lanyu)
    diffraction_loss_result = twterrain.diffraction_loss_from_profile(tx1_wangyou_pavilion, tx5_lanyu)
    
    # PA gain = 52 db, 考慮 p1db, 打 -2 dbm, PA gain = 47 db 上下
    # tx antenna = 6.8 dbi, 先不考慮 tx 天線增益
    # rx antenna = 2.15 dbi, 先不考慮 rx 天線增益
    # rx gain = 0 db, rx 沒有 LNA
    # miscellaneous loss 先抓 3 db
    # 如果要在 correlation 圖看到訊號, 接收功率起碼大於 -121dbm, 才可以看到約 10 db 的 peak
    received_power_result = twterrain.received_power_dbm(tx1_wangyou_pavilion, tx5_lanyu, -2, 47, 0, 3)