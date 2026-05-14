# iGPS 模擬器 — 實作計畫

## 概述

建立一套 Python 桌面應用程式，可模擬台灣陸地上任意兩站基地台之間的無線電訊號傳播。核心功能包括：

1. 載入 20m 解析度台灣 DEM (GeoTIFF, TWD97 TM2)
2. WGS84 ↔ TWD97 TM2 座標互轉
3. 兩站間地形剖面取樣 + 升取樣 (20m / 10m / 5m / 1m)
4. 視線 (LOS) 判定（含地球曲率校正）
5. 第一菲涅爾區 (1st Fresnel Zone) 淨空分析（377.5 MHz）
6. 地形繞射損耗 (Terrain Diffraction Loss) — Deygout 遞迴多刃法
7. 接收功率計算（FSPL + Diffraction Loss）
8. GUI：輸入面板 + 台灣互動地圖 + 剖面圖 + 結果面板

---

## User Review Required

> [!IMPORTANT]
> **UI 框架選擇**：計畫使用 **Tkinter** (Python 內建) 搭配 Matplotlib 嵌入剖面圖、以及 Folium 產生互動地圖 (以 HTML 嵌入 Tkinter WebView)。如果你更偏好 PyQt5 或其他框架請告知。

> [!IMPORTANT]
> **Terrain Diffraction Loss 方法選擇 — Deygout 遞迴多刃法**
>
> 我推薦使用 **Deygout 遞迴多刃法 (Deygout Recursive Multiple Knife-Edge Method)**，原因如下：
>
> | 項目 | 說明 |
> |------|------|
> | **優點** | 1. ITU-R P.526 推薦方法之一，業界廣泛使用<br>2. 可處理多個遮蔽物，比單一刃峰模型更準確<br>3. 演算法簡潔、易於實作與除錯<br>4. 對 VHF/UHF 頻段 (如 377.5 MHz) 適用性佳 |
> | **缺點** | 1. 在多障礙物且彼此距離很近時，可能略為高估損耗<br>2. 不考慮障礙物的圓弧頂部 (rounded obstacle)，只做刃峰近似 |
> | **適用性** | ✅ 本專案為 VHF 頻段 (377.5 MHz)，台灣地形多山脈，Deygout 方法能有效處理多山脊遮蔽情境 |
>
> 若日後需要更高精度，可擴充為 **ITU-R P.526 中的 Bullington + Spherical Earth Diffraction** 方法。

---

## 資料夾架構

```
2026-iGPS-Simulator/
├── main.py                      # 程式進入點
├── requirements.txt             # 套件依賴
├── config.py                    # 全域設定 (DEM 路徑、頻率、地球半徑等)
├── Readme.md
│
├── core/                        # 核心計算模組
│   ├── __init__.py
│   ├── dem_loader.py            # DEM 檔案載入 (rasterio)
│   ├── coordinate.py            # WGS84 ↔ TWD97 TM2 座標轉換
│   ├── terrain_profile.py       # 地形剖面取樣 & 升取樣
│   ├── earth_curvature.py       # 地球曲率校正
│   ├── los_analysis.py          # LOS 判定
│   ├── fresnel.py               # Fresnel Zone 淨空計算
│   ├── diffraction.py           # 繞射損耗 (Deygout)
│   └── link_budget.py           # 接收功率計算 (FSPL + Diffraction)
│
├── visualization/               # 繪圖模組
│   ├── __init__.py
│   ├── profile_plot.py          # 剖面圖 (matplotlib)
│   └── map_view.py              # 台灣互動地圖 (folium)
│
└── ui/                          # GUI 模組
    ├── __init__.py
    ├── app.py                   # 主視窗 (Tkinter)
    ├── input_panel.py           # 左側輸入面板
    ├── result_panel.py          # 右側結果面板
    └── map_panel.py             # 地圖 + 剖面圖面板
```

---

## Proposed Changes

### 1. 設定與依賴

#### [NEW] [requirements.txt](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/requirements.txt)

```
rasterio          # GeoTIFF 讀取
pyproj            # 座標轉換
numpy             # 數值計算
scipy             # 內插法升取樣
matplotlib        # 剖面圖繪製
folium            # 互動地圖
tkhtmlview        # 在 Tkinter 中嵌入 HTML (顯示 folium 地圖)
```

#### [NEW] [config.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/config.py)

全域常數：
- `DEM_PATH`: TIF 檔案路徑
- `FREQUENCY_MHZ = 377.5`
- `EARTH_RADIUS_M = 6_371_000` (標準地球半徑)
- `K_FACTOR = 4/3` (等效地球半徑因子)
- `EFFECTIVE_EARTH_RADIUS = EARTH_RADIUS_M * K_FACTOR`
- `NO_DATA_VALUE = -32767` (海上高度替換為 0)
- `RESOLUTION_OPTIONS = {20: "原始精度", 10: "10m", 5: "5m", 1: "1m"}`

---

### 2. 核心計算模組 (`core/`)

#### [NEW] [dem_loader.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/core/dem_loader.py)

**`class DEMLoader`**
- `__init__(self, dem_path)`: 使用 `rasterio.open()` 載入 DEM
- `get_elevation(self, x_twd97, y_twd97) -> float`: 查詢單點海拔，若為 -32767 則回傳 0
- `get_transform()`: 取得 affine transform 供座標轉換
- `get_crs()`: 取得 CRS 資訊
- 使用 `rasterio` 讀取 band 1

#### [NEW] [coordinate.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/core/coordinate.py)

**`class CoordinateConverter`**
- 使用 `pyproj.Transformer`
- `wgs84_to_twd97(self, lon, lat) -> (x, y)`: WGS84 (EPSG:4326) → TWD97 TM2 (EPSG:3826)
- `twd97_to_wgs84(self, x, y) -> (lon, lat)`: 反轉
- `__init__` 中建立 `Transformer.from_crs("EPSG:4326", "EPSG:3826", always_xy=True)`

#### [NEW] [terrain_profile.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/core/terrain_profile.py)

**`class TerrainProfiler`**
- `__init__(self, dem_loader: DEMLoader, coord_converter: CoordinateConverter)`
- `extract_profile(self, lon1, lat1, lon2, lat2, resolution_m: int) -> TerrainProfile`:
  - 將經緯度轉為 TWD97
  - 計算兩點間的距離
  - 依照 `resolution_m` 決定取樣點數 (`num_samples = total_distance / resolution_m`)
  - 在兩點間等距取樣 TWD97 座標
  - 使用 `rasterio.sample()` 取得原始高程 (20m 精度)
  - 若 `resolution_m < 20`: 使用 `scipy.interpolate.interp1d(kind='cubic')` 做升取樣 (cubic interpolation)
  - 回傳 `TerrainProfile` dataclass

**`@dataclass TerrainProfile`**
- `distances: np.ndarray` — 各取樣點到起點的距離 (m)
- `elevations: np.ndarray` — 各取樣點的海拔 (m)
- `coords_twd97: list[tuple]` — TWD97 座標
- `resolution_m: int`
- `total_distance: float`

#### [NEW] [earth_curvature.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/core/earth_curvature.py)

**`class EarthCurvature`**
- `__init__(self, effective_radius)`: 使用 `EFFECTIVE_EARTH_RADIUS`
- `correction(self, d1, d2) -> float`: 計算距離 d1 和 d2 處的地球曲率校正值
  - 公式: `h_curve = (d1 * d2) / (2 * R_eff)`
  - 其中 d1 = 取樣點到發射端距離, d2 = 取樣點到接收端距離
- `apply_correction(self, profile: TerrainProfile) -> np.ndarray`: 對整個剖面加上曲率校正

#### [NEW] [los_analysis.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/core/los_analysis.py)

**`class LOSAnalyzer`**
- `__init__(self, earth_curvature: EarthCurvature)`
- `analyze(self, profile: TerrainProfile, h_ant1: float, h_ant2: float) -> LOSResult`:
  - 計算含曲率校正的地形高度
  - 建立視線直線 (從 站1海拔+天線高 到 站2海拔+天線高)
  - 對每個中間取樣點判斷地形是否高於視線 (**排除端點**)
  - 記錄所有遮蔽點

**`@dataclass LOSResult`**
- `is_clear: bool`
- `los_heights: np.ndarray` — 視線高度陣列
- `terrain_corrected: np.ndarray` — 曲率校正後地形高度
- `obstruction_indices: list[int]` — 遮蔽點索引
- `max_obstruction_height: float` — 最大遮蔽高度

#### [NEW] [fresnel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/core/fresnel.py)

**`class FresnelCalculator`**
- `__init__(self, frequency_mhz, earth_curvature: EarthCurvature)`
- `wavelength` 屬性: `c / f`
- `first_fresnel_radius(self, d1, d2) -> float`: 第一菲涅爾區半徑
  - 公式: `r = sqrt(lambda * d1 * d2 / (d1 + d2))`
- `analyze(self, profile: TerrainProfile, los_result: LOSResult) -> FresnelResult`:
  - 對每個中間取樣點 (**排除端點**) 計算第一菲涅爾半徑
  - 計算淨空比 (clearance ratio) = (視線高度 - 地形高度) / 菲涅爾半徑
  - 若任一點淨空比 < 1.0，代表菲涅爾區被侵入

**`@dataclass FresnelResult`**
- `clearance_ratios: np.ndarray`
- `fresnel_radii: np.ndarray`
- `min_clearance_ratio: float`
- `min_clearance_index: int`
- `is_clear: bool` (min_clearance_ratio >= 1.0)

#### [NEW] [diffraction.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/core/diffraction.py)

**`class DiffractionCalculator`** — Deygout 遞迴多刃法

- `__init__(self, frequency_mhz, earth_curvature: EarthCurvature)`
- `_knife_edge_loss(self, nu) -> float`:
  - `if nu <= -0.78: return 0`
  - `else: return 6.9 + 20 * log10(sqrt((nu-0.1)^2 + 1) + nu - 0.1)`
- `_calc_nu(self, h, d1, d2, wavelength) -> float`:
  - `nu = h * sqrt(2 / (wavelength) * (1/d1 + 1/d2))`
  - h 為障礙物頂部相對於視線的高度 (正值=遮蔽)
- `_deygout_recursive(self, distances, terrain_corrected, h_start, h_end, start_idx, end_idx) -> float`:
  - 在 `[start_idx+1, end_idx-1]` 範圍中 (排除端點) 找出 ν 最大的障礙物
  - 若 ν_max <= -0.78，回傳 0
  - 否則回傳 `loss(ν_max) + 遞迴(左半段) + 遞迴(右半段)`
- `calculate(self, profile, los_result) -> DiffractionResult`

**`@dataclass DiffractionResult`**
- `total_loss_db: float`
- `dominant_edge_index: int`
- `dominant_edge_nu: float`

#### [NEW] [link_budget.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/core/link_budget.py)

**`class LinkBudgetCalculator`**
- `free_space_path_loss(self, distance_m, frequency_mhz) -> float`:
  - FSPL(dB) = `20*log10(d) + 20*log10(f) + 32.44` (d in km, f in MHz)
- `received_power(self, tx_power_dbm, tx_gain_dbi, rx_gain_dbi, fspl_db, diffraction_loss_db) -> float`:
  - `Prx = Ptx + Gtx + Grx - FSPL - DiffractionLoss`

---

### 3. 繪圖模組 (`visualization/`)

#### [NEW] [profile_plot.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/visualization/profile_plot.py)

**`class ProfilePlotter`**
- `plot(self, fig, profile, los_result, fresnel_result, h_ant1, h_ant2)`:
  - 繪製地形剖面 (填充)
  - 繪製 LOS 直線
  - 繪製第一菲涅爾區上下邊界 (虛線)
  - 用紅色標記遮蔽區域
  - 標注兩站海拔 + 天線高度
  - 橫軸: 距離 (km), 縱軸: 海拔 (m)
  - **不需要** 平移和縮放功能

#### [NEW] [map_view.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/visualization/map_view.py)

**`class MapViewer`**
- `create_map(self, station1_latlon, station2_latlon, is_obstructed) -> str`:
  - 使用 `folium.Map` 建立台灣地圖
  - 加入兩站 Marker (顯示座標 + 海拔)
  - 加入連線 PolyLine (綠色=LOS clear, 紅色=obstructed)
  - 回傳 HTML 字串
  - 地圖支援平移和縮放 (folium 內建功能)

---

### 4. GUI 模組 (`ui/`)

#### [NEW] [app.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/app.py)

**`class SimulatorApp`** — Tkinter 主視窗
- 佈局：三欄式
  - **左欄**: `InputPanel` — 座標、天線高度、精度、功率參數輸入
  - **中欄**: 地圖 (上) + 剖面圖 (下)
  - **右欄**: `ResultPanel` — 計算結果顯示
- 「模擬」按鈕觸發完整計算流程

#### [NEW] [input_panel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/input_panel.py)

**`class InputPanel`**
- 站 A: 經度、緯度、天線高度 (m) 輸入欄位
- 站 B: 經度、緯度、天線高度 (m) 輸入欄位
- 精度選擇: 下拉式選單 (20m / 10m / 5m / 1m)
- 功率參數:
  - 發射功率 (dBm)
  - 發射端天線增益 (dBi)
  - 接收端天線增益 (dBi)
- 「開始模擬」按鈕

#### [NEW] [result_panel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/result_panel.py)

**`class ResultPanel`**
- 站 A 海拔 / 站 B 海拔
- 兩站距離
- LOS 判定結果 (✅ / ❌)
- 頻率: 377.5 MHz
- 第一菲涅爾區最小淨空比
- 菲涅爾區淨空判定 (✅ / ❌)
- 繞射損耗 (dB)
- 自由空間損耗 (dB)
- 接收功率 (dBm)

#### [NEW] [map_panel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/map_panel.py)

**`class MapPanel`**
- 上方: 嵌入 folium HTML 地圖 (使用 `tkhtmlview.HTMLLabel`)
- 下方: 嵌入 matplotlib 剖面圖 (使用 `FigureCanvasTkAgg`)

---

### 5. 進入點

#### [NEW] [main.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/main.py)

- 初始化所有模組（依賴注入）
- 啟動 `SimulatorApp`

---

## 關鍵技術細節

### 地球曲率校正

所有 LOS、Fresnel、Diffraction 計算都使用統一的地球曲率校正：

```
h_corrected(i) = h_terrain(i) + d1(i) * d2(i) / (2 * R_eff)
```

其中 `R_eff = 6,371,000 × 4/3 = 8,494,667 m`

### 升取樣策略

- 先以 20m 解析度取樣原始 DEM 點
- 若目標精度 < 20m，使用 `scipy.interpolate.interp1d(kind='cubic')` 對距離-海拔資料做內插
- 僅在兩站連線上做升取樣，不處理整張地圖

### 端點排除

依據需求 #15，在 Fresnel 和 Diffraction 計算中，排除起點和終點 (即基地台所在位置)，只對中間的取樣點做分析。

---

## Verification Plan

### Automated Tests

1. **單元測試** — 測試座標轉換正確性 (已知台北座標 WGS84 ↔ TWD97)
2. **單元測試** — 測試 FSPL 公式 (與已知值比對)
3. **單元測試** — 測試 Fresnel 半徑計算
4. **單元測試** — 測試 Deygout 單刃計算
5. **整合測試** — 使用已知兩點執行完整模擬流程

### Manual Verification

1. 啟動 GUI，輸入台北 (25.033, 121.565) 與高雄 (22.627, 120.301) 座標
2. 確認地圖正確顯示兩站位置與連線
3. 確認剖面圖合理呈現台灣南北向地形
4. 測試海上座標 (如離島) 是否正確處理為海拔 0
5. 比較不同精度 (20m vs 1m) 的結果差異
