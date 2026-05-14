# iGPS 無線電傳播模擬器 — 完成摘要

## 已完成項目

已建立完整的 Python 桌面應用程式，共 **17 個檔案**，結構如下：

```
2026-iGPS-Simulator/
├── main.py                      # 程式進入點
├── config.py                    # 全域常數設定
├── requirements.txt             # 套件依賴
├── test_integration.py          # 整合測試
├── core/                        # 核心計算 (8 模組)
│   ├── dem_loader.py            # DEM GeoTIFF 載入
│   ├── coordinate.py            # WGS84 ↔ TWD97 TM2 轉換
│   ├── terrain_profile.py       # 地形剖面 + 升取樣
│   ├── earth_curvature.py       # 地球曲率校正 (k=4/3)
│   ├── los_analysis.py          # 視線判定
│   ├── fresnel.py               # Fresnel 淨空分析
│   ├── diffraction.py           # Deygout 繞射損耗
│   └── link_budget.py           # FSPL + 接收功率
├── visualization/               # 繪圖 (2 模組)
│   ├── profile_plot.py          # matplotlib 剖面圖
│   └── map_view.py              # folium 互動地圖
└── ui/                          # GUI (4 模組)
    ├── input_panel.py           # 輸入面板
    ├── result_panel.py          # 結果面板
    ├── map_panel.py             # 地圖+剖面圖面板
    └── app.py                   # 主視窗
```

## 核心功能對應 Readme 需求

| # | 需求 | 實作 |
|---|------|------|
| 1 | 載入台灣 DEM | `DEMLoader` — rasterio 讀取 GeoTIFF |
| 2 | TWD97 TM2 座標系統 | `CoordinateConverter` — pyproj EPSG:3826 ↔ 4326 |
| 3 | 升取樣 (20/10/5/1m) | `TerrainProfiler` — scipy cubic interpolation |
| 4 | UI 輸入 + 精度選單 | `InputPanel` — 兩站座標/天線高/精度/功率 |
| 5 | 台灣互動地圖 | `MapViewer` — folium + tkhtmlview 嵌入 |
| 6 | 剖面圖 | `ProfilePlotter` — matplotlib 嵌入 Tkinter |
| 7 | Fresnel clearance | `FresnelCalculator` — 377.5 MHz, 結果顯示在右欄 |
| 8 | 接收功率計算 | `LinkBudgetCalculator` — FSPL + diffraction |
| 9 | Terrain diffraction | `DiffractionCalculator` — Deygout 遞迴多刃法 |
| 10 | Python | ✅ |
| 11 | OOP/SOLID 模組化 | ✅ 依賴注入、單一職責、開放封閉 |
| 12 | 資料夾架構 | ✅ core/ visualization/ ui/ |
| 13 | 海上座標處理 | `DEMLoader` — -32767 → 0 |
| 14 | 地圖平移縮放 | folium 內建功能 |
| 15 | 端點排除 | LOS/Fresnel/Diffraction 均排除 index 0 和 n-1 |
| 16 | 地球曲率 | `EarthCurvature` — 統一 k=4/3, R_eff = 8,494,667m |
| 17 | 程式碼註解 | ✅ 所有模組含中文 docstring |

## 測試結果

### 模組匯入: 11/11 通過

### 整合測試

| 測試案例 | 結果 |
|---------|------|
| 短距離 (台北 925m) | LOS ✅, Fresnel 淨空比 2.2, Rx -31.3 dBm |
| 長距離 (台北→高雄 296km) | LOS ❌, 遮蔽 4550m (中央山脈), 繞射 149.78 dB |
| 海上座標 | 正確回傳 0.0m |

## 使用方式

```bash
cd c:\Users\genui\Documents\Projects\2026-iGPS-Simulator
python main.py
```
