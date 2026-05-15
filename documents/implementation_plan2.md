# Tkinter → PyQt6 遷移計畫

將 iGPS 模擬器的 GUI 從 Tkinter 遷移至 PyQt6，解決 tkhtmlview 無法渲染 folium 地圖（需要 JavaScript）的問題。

## 核心動機

PyQt6 的 `QWebEngineView`（基於 Chromium）可以直接在應用程式內嵌入渲染 folium 產生的互動地圖，不再需要外開瀏覽器。

## 不變的模組

以下模組**不需修改**，維持原樣：
- `config.py` — 全域設定
- `core/` — 所有核心計算模組（DEM、座標、地形剖面、繞射、LOS 等）
- `visualization/map_view.py` — folium 地圖生成（產出 HTML 字串）
- `visualization/profile_plot.py` — matplotlib 剖面圖繪製（使用 Figure API，與 backend 無關）
- `stations.json` — 站點資料

## Proposed Changes

### 依賴更新

#### [MODIFY] [requirements.txt](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/requirements.txt)
- 新增 `PyQt6>=6.5.0` 和 `PyQt6-WebEngine>=6.5.0`
- 移除不再需要的 tkhtmlview（目前未列入 requirements.txt，但確認不需要）

---

### 主程式入口

#### [MODIFY] [main.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/main.py)
- 改用 `QApplication` 取代 `tk.Tk()`
- 建立 `QApplication` → `SimulatorApp` → `app.exec()`

---

### UI 模組 — 完整重寫

#### [MODIFY] [app.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/app.py)
- `SimulatorApp` 改繼承 `QMainWindow`
- 使用 `QSplitter` 實現三欄式佈局（左: InputPanel / 中: MapPanel / 右: ResultPanel）
- 核心計算模組初始化不變
- `_run_simulation()` 邏輯不變，僅更新 UI 呼叫方式
- 錯誤對話框改用 `QMessageBox`

#### [MODIFY] [map_panel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/map_panel.py)
- **重點改動**：使用 `QWebEngineView` 取代外開瀏覽器
- 上半部：`QWebEngineView` 直接嵌入 folium 地圖（`setHtml(html_content)`）
- 下半部：matplotlib 改用 `FigureCanvasQTAgg` backend（`matplotlib.backends.backend_qtagg`）
- 使用 `QSplitter(Qt.Orientation.Vertical)` 分割地圖與剖面圖

#### [MODIFY] [input_panel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/input_panel.py)
- 改用 `QGroupBox` + `QFormLayout` 建立表單
- `tk.StringVar` → `QLineEdit.text()` / `QComboBox.currentText()`
- 模擬按鈕用 `QPushButton`
- 狀態列用 `QLabel`
- 介面佈局、欄位名稱、預設值維持一致

#### [MODIFY] [result_panel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/result_panel.py)
- 改用 `QGroupBox` + `QFormLayout` 取代 `ttk.LabelFrame` + grid
- 結果值用 `QLabel` 字典存取（與原 `_result_vars` 模式類似）
- 放入 `QScrollArea` 避免內容溢出

#### [MODIFY] [station_dialog.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/station_dialog.py)
- 改用 `QDialog` + `QTableWidget` 取代 `tk.Toplevel` + `ttk.Treeview`
- Modal 行為用 `dialog.exec()` 實現
- 雙擊選擇、確定/取消按鈕功能維持

---

## 佈局對照

| 原 Tkinter | 新 PyQt6 |
|---|---|
| `tk.Tk()` | `QMainWindow` |
| `ttk.PanedWindow` | `QSplitter` |
| `ttk.LabelFrame` | `QGroupBox` |
| `ttk.Entry` / `tk.StringVar` | `QLineEdit` |
| `ttk.Combobox` | `QComboBox` |
| `ttk.Button` | `QPushButton` |
| `ttk.Label` | `QLabel` |
| `ttk.Treeview` | `QTableWidget` |
| `tk.Toplevel` (modal) | `QDialog` |
| `messagebox.showerror` | `QMessageBox.critical` |
| `FigureCanvasTkAgg` | `FigureCanvasQTAgg` |
| 外開瀏覽器 (`webbrowser`) | `QWebEngineView.setHtml()` |

## Verification Plan

### Automated Tests
- `pip install PyQt6 PyQt6-WebEngine` 確認安裝成功
- `python -c "from PyQt6.QtWidgets import QApplication; from PyQt6.QtWebEngineWidgets import QWebEngineView; print('OK')"` 確認 import 正常

### Manual Verification
- 執行 `python main.py` 啟動應用程式
- 確認三欄式佈局正確顯示
- 確認 folium 地圖可在應用內直接渲染（無需外開瀏覽器）
- 確認剖面圖正常顯示
- 確認載入座標對話框正常運作
