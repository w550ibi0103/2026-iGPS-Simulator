# iGPS Simulator — 任務追蹤

## 1. 基礎設定
- [x] requirements.txt
- [x] config.py

## 2. 核心計算模組 (core/)
- [x] core/__init__.py
- [x] core/dem_loader.py
- [x] core/coordinate.py
- [x] core/terrain_profile.py
- [x] core/earth_curvature.py
- [x] core/los_analysis.py
- [x] core/fresnel.py
- [x] core/diffraction.py
- [x] core/link_budget.py

## 3. 繪圖模組 (visualization/)
- [x] visualization/__init__.py
- [x] visualization/profile_plot.py
- [x] visualization/map_view.py

## 4. GUI 模組 (ui/)
- [x] ui/__init__.py
- [x] ui/input_panel.py
- [x] ui/result_panel.py
- [x] ui/map_panel.py
- [x] ui/app.py

## 5. 進入點
- [x] main.py

## 6. 驗證
- [x] 安裝依賴
- [x] 模組匯入測試 (11/11 全通過)
- [x] DEM 載入測試 (台北 8.8m, 高雄 3.1m)
- [x] 整合測試 (短距離 LOS暢通, 長距離 LOS遮蔽, 海上座標處理)
- [x] GUI 啟動測試
