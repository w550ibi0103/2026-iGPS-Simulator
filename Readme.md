# iGPS 無線電傳播模擬器 - 系統說明文件

本文件詳細說明 iGPS 系統中各核心模組的功能、內部參數、方法型別，以及系統中所使用的物理與數學原理，最後說明整體的系統架構與執行流程。

---

## 1. 模組主要功能與參數、方法說明

### 1.1 `core.earth_curvature` (地球曲率校正模組)
* **主要功能**: 提供地球曲率對地形高程的校正計算。考量大氣折射效應，使電磁波的彎曲路徑可以用直線來等效分析。
* **`EarthCurvature` 物件**:
  * **參數**:
    * `effective_radius` (float): 等效地球半徑 (公尺)。這個值通常等於 $R_{earth} \times k$，其中 $k$ 為**等效地球半徑因子** (預設為 4/3，代表標準大氣折射)。
  * **方法**:
    * `correction(d1: float, d2: float) -> float`: 計算單一點的地球曲率校正值。輸入為該點距發射端 (`d1`) 與接收端 (`d2`) 的距離，輸出為應增加的海拔高度。
    * `apply_correction(distances: np.ndarray, elevations: np.ndarray) -> np.ndarray`: 對整條地形剖面批次套用校正，回傳校正後的海拔陣列。

### 1.2 `core.dem_loader` (DEM 載入模組)
* **主要功能**: 讀取 GeoTIFF 格式的數位高程模型 (DEM) 檔案，提供座標對應的海拔查詢功能。
* **`DEMLoader` 物件**:
  * **參數**: 無公開屬性，內部維護 DEM 檔案的數據矩陣、座標系統與轉換矩陣 (Transform)。
  * **方法**:
    * `get_elevation(x_twd97: float, y_twd97: float) -> float`: 輸入 TWD97 X/Y 座標 (公尺)，輸出對應的海拔高度 (公尺)。若超出範圍或在海上，回傳海平面 0。
    * `get_elevations_batch(coords: list) -> np.ndarray`: 輸入包含多個 `(x, y)` 座標的列表，回傳對應的海拔高度一維陣列。

### 1.3 `core.coordinate` (座標轉換模組)
* **主要功能**: 提供 WGS84 (經緯度) 與 TWD97 TM2 (投影座標) 之間的高精度雙向轉換。
* **`CoordinateConverter` 物件**:
  * **方法**:
    * `wgs84_to_twd97(lon: float, lat: float) -> tuple`: 輸入 WGS84 的經緯度，輸出 TWD97 的 `(easting_x, northing_y)` 座標。
    * `twd97_to_wgs84(x: float, y: float) -> tuple`: 輸入 TWD97 座標，輸出 WGS84 的 `(longitude, latitude)`。

### 1.4 `core.terrain_profile` (地形剖面取樣模組)
* **主要功能**: 在兩站連線上等距取樣地形高程，並支援 Cubic Interpolation 進行升取樣 (如將 20m 精度提升至 10m、5m、1m)。
* **`TerrainProfiler` 物件**:
  * **方法**:
    * `extract_profile(lon1, lat1, lon2, lat2, resolution_m) -> TerrainProfile`: 輸入兩站經緯度與目標解析度，輸出 `TerrainProfile` 資料類別 (包含距離陣列 `distances`、高程陣列 `elevations`、總距離等屬性)。

### 1.5 `core.los_analysis` (視線 LOS 分析模組)
* **主要功能**: 判斷兩站基地台之間的直線是否被地形遮蔽。
* **`LOSAnalyzer` 物件**:
  * **方法**:
    * `analyze(profile: TerrainProfile, h_ant1: float, h_ant2: float) -> LOSResult`: 依據地形剖面與兩端天線高度，計算視線是否被遮蔽，輸出 `LOSResult` 資料類別 (包含布林值 `is_clear`、視線高度陣列 `los_heights`、最大遮蔽高度等)。

### 1.6 `core.fresnel` (第一菲涅爾區淨空分析模組)
* **主要功能**: 計算各取樣點的第一菲涅爾區半徑，並判斷地形是否侵入菲涅爾區。
* **`FresnelCalculator` 物件**:
  * **參數**:
    * `wavelength` (float): 電磁波波長 (公尺)。
  * **方法**:
    * `first_fresnel_radius(d1: float, d2: float) -> float`: 輸入距兩端距離，輸出該點的第一菲涅爾區半徑。
    * `analyze(profile: TerrainProfile, los_result: LOSResult) -> FresnelResult`: 分析地形是否侵入，輸出 `FresnelResult` 資料類別 (包含各點淨空比 `clearance_ratios`、最小淨空比 `min_clearance_ratio` 等)。

### 1.7 `core.diffraction` (地形繞射損耗計算模組)
* **主要功能**: 使用 ITU-R P.526 推薦的 Deygout 方法計算多障礙物繞射損耗 (迭代版)。
* **`DiffractionCalculator` 物件**:
  * **參數**:
    * `wavelength` (float): 波長 (公尺)。
  * **方法**:
    * `knife_edge_loss(nu: float) -> float`: 計算單一刃峰損耗。
    * `calculate(profile: TerrainProfile, los_result: LOSResult, h_ant1: float, h_ant2: float) -> DiffractionResult`: 計算整段路徑的總繞射損耗，輸出包含 `total_loss_db` 等資訊的結果。

### 1.8 `core.link_budget` (鏈路預算計算模組)
* **主要功能**: 綜合設備參數與路徑損耗，計算最終接收功率。
* **`LinkBudgetCalculator` 物件**:
  * **參數**:
    * `frequency_mhz` (float): 運作頻率 (MHz)。
  * **方法**:
    * `received_power(tx_power_dbm, tx_gain_dbi, rx_gain_dbi, distance_m, diffraction_loss_db) -> LinkBudgetResult`: 計算自由空間路徑損耗 (FSPL) 並扣除繞射損耗，輸出接收功率。

---

## 2. 數學與物理原理詳細解釋

### 2.1 地球曲率校正與等效地球半徑 ($k$ 因子)
由於大氣折射率隨高度變化，電磁波在空氣中傳播時路徑會向下彎曲。為了便於計算，我們假設電磁波是直線傳播，而將地球的半徑放大為 $R_{eff} = R_{earth} \times k$。在標準大氣下，$k \approx 4/3$。
地形校正公式如下：
$$h_{curve} = \frac{d_1 \times d_2}{2 R_{eff}}$$
* $d_1$: 取樣點到發射端的距離。
* $d_2$: 取樣點到接收端的距離。
此校正值 $h_{curve}$ 會疊加在原始的 DEM 地形高度上，形成等效的彎曲地形。

### 2.2 第一菲涅爾區 (1st Fresnel Zone)
菲涅爾區是電磁波傳播的主要能量通道。第一菲涅爾區包含了 50% 以上的傳輸能量。如果在第一菲涅爾區內沒有障礙物，傳播特性就近似於自由空間。
半徑計算公式：
$$r_1 = \sqrt{\frac{\lambda \times d_1 \times d_2}{d_1 + d_2}}$$
* $\lambda$: 電磁波波長。
實務上，只要障礙物不侵入第一菲涅爾區半徑的 60% (即淨空比 clearance ratio $\ge 0.6$)，即認為達到「淨空」標準。

### 2.3 繞射損耗與 Fresnel-Kirchhoff 參數 ($\nu$)
當地形遮蔽視線時，電磁波會因繞射而產生損耗。這裡採用 ITU-R P.526 推薦的單刃峰模型。
首先計算障礙物的 Fresnel-Kirchhoff 繞射參數 $\nu$：
$$\nu = h \sqrt{\frac{2}{\lambda} \left(\frac{1}{d_1} + \frac{1}{d_2}\right)}$$
* $h$: 障礙物頂部相對於兩端點連線 (視線) 的高度 (正值代表遮蔽)。

單一刃峰的繞射損耗 $J(\nu)$ dB 近似公式：
* 當 $\nu \le -0.78$ 時：$J(\nu) = 0$
* 當 $\nu > -0.78$ 時：$J(\nu) = 6.9 + 20 \log_{10}\left(\sqrt{(\nu - 0.1)^2 + 1} + \nu - 0.1\right)$

對於**多障礙物 (Deygout 法)**，系統採用迭代方式：
1. 找出路徑中 $\nu$ 值最大的主要障礙物，計算其損耗 $J_1$。
2. 將該障礙物作為新的端點，把路徑切為左右兩半。
3. 對左右子路徑重複尋找最大障礙物並計算損耗。
4. 總繞射損耗為所有障礙物損耗之總和。

### 2.4 鏈路預算 (Link Budget)
首先計算自由空間路徑損耗 (FSPL)，公式為：
$$FSPL(dB) = 20 \log_{10}(d_{km}) + 20 \log_{10}(f_{MHz}) + 32.44$$
最終接收功率 $P_{rx}$ (dBm) 計算方式：
$$P_{rx} = P_{tx} + G_{tx} + G_{rx} - FSPL - L_{diffraction}$$
* $P_{tx}$: 發射功率 (dBm)
* $G_{tx}, G_{rx}$: 發射與接收天線增益 (dBi)
* $L_{diffraction}$: 地形造成的總繞射損耗 (dB)

---

## 3. 系統架構與執行流程

### 3.1 系統架構設計
系統採用模組化與依賴注入 (Dependency Injection) 的設計模式：
* **核心計算層 (`core`)**: 包含 `DEMLoader`, `TerrainProfiler`, `LOSAnalyzer` 等，純粹負責資料處理與物理計算，互不依賴 UI。
* **視覺化層 (`visualization`)**: `ProfilePlotter` 負責繪製 2D 剖面圖 (Matplotlib)，`MapViewer` 負責產生互動式地圖 (Folium)。
* **UI 控制層 (`ui.app.SimulatorApp`)**: 作為主要的 Controller，負責實例化所有核心模組，並協調整個資料流與介面更新。

### 3.2 程式執行流程
當使用者於介面點擊「開始模擬」按鈕後，會觸發 `SimulatorApp._run_simulation()`，執行流程如下：

1. **參數獲取**: 從 UI 的 `InputPanel` 取得兩站經緯度、天線高度、取樣精度、系統增益等參數。
2. **地形剖面提取**: 
   * 呼叫 `TerrainProfiler.extract_profile()`。
   * 將經緯度透過 `CoordinateConverter` 轉為 TWD97 座標。
   * 根據總距離與解析度，利用 `DEMLoader` 批次查詢海拔。若設定為高精度，則使用 Cubic Interpolation 進行升取樣，最終回傳 `TerrainProfile` 物件。
3. **曲率校正與視線分析**: 
   * 將 `TerrainProfile` 傳入 `LOSAnalyzer.analyze()`。
   * 內部呼叫 `EarthCurvature` 將地球曲率疊加至原始地形，然後透過線性內插建立視線高度，比對是否產生遮蔽，回傳 `LOSResult`。
4. **菲涅爾區檢查**: 
   * 將剖面與 LOS 結果傳入 `FresnelCalculator.analyze()`，計算每一點的 $r_1$ 半徑與淨空比，找出最差淨空點位置，回傳 `FresnelResult`。
5. **繞射損耗計算**: 
   * 將資料傳入 `DiffractionCalculator.calculate()`，使用 Deygout 迭代演算法尋找主要障礙物，並累加各障礙物的刀鋒損耗，回傳 `DiffractionResult`。
6. **接收功率結算**: 
   * 將總距離、繞射損耗與設備參數交由 `LinkBudgetCalculator.received_power()` 處理，計算 FSPL 與最終接收功率 (dBm)。
7. **結果渲染與回饋**: 
   * 呼叫 `ProfilePlotter.plot()` 繪製地形、視線與菲涅爾區的 2D 剖面圖。
   * 呼叫 `MapViewer.create_map()` 產生帶有連線與最差點標示的互動式地圖，並更新 WebEngine 畫面。
   * 更新右側 `ResultPanel` 的各項數值與狀態指標，完成單次模擬流程。
