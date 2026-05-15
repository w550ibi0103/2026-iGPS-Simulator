# Walkthrough: Tkinter → PyQt6 遷移

## 動機

原有的 Tkinter GUI 無法內嵌 folium 地圖（tkhtmlview 不支援 JavaScript），只能外開瀏覽器。改用 PyQt6 後，`QWebEngineView`（基於 Chromium）可直接在應用程式內渲染完整的互動地圖。

## 修改的檔案

| 檔案 | 變更摘要 |
|---|---|
| [requirements.txt](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/requirements.txt) | 新增 `PyQt6>=6.5.0`、`PyQt6-WebEngine>=6.5.0` |
| [main.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/main.py) | `tk.Tk()` → `QApplication` + `app.exec()` |
| [ui/app.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/app.py) | `SimulatorApp` 從繼承無 → 繼承 `QMainWindow`；用 `QSplitter` 三欄佈局；`messagebox` → `QMessageBox` |
| [ui/map_panel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/map_panel.py) | **核心改動**：`QWebEngineView.setHtml()` 取代外開瀏覽器；matplotlib backend 改用 `FigureCanvasQTAgg` |
| [ui/input_panel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/input_panel.py) | `ttk.LabelFrame`+grid → `QGroupBox`+`QFormLayout`；`tk.StringVar` → `QLineEdit` |
| [ui/result_panel.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/result_panel.py) | 同上，加入 `QScrollArea` 防溢出 |
| [ui/station_dialog.py](file:///c:/Users/genui/Documents/Projects/2026-iGPS-Simulator/ui/station_dialog.py) | `tk.Toplevel` → `QDialog`；`ttk.Treeview` → `QTableWidget` |

## 未修改的模組

- `config.py` — 全域設定不變
- `core/` — 所有計算邏輯不變
- `visualization/` — folium 地圖生成和 matplotlib 剖面圖繪製不變
- `stations.json` — 站點資料不變

## 驗證結果

- ✅ `pip install PyQt6 PyQt6-WebEngine` 安裝成功 (v6.11.0)
- ✅ `from PyQt6.QtWidgets import QApplication; from PyQt6.QtWebEngineWidgets import QWebEngineView` import 正常
- ✅ 所有 7 個修改檔案通過 `py_compile` 語法檢查

## 啟動方式

```bash
python main.py
```

與原來相同，無需額外步驟。
