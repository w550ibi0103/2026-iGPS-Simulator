# -*- coding: utf-8 -*-
"""
iGPS 無線電傳播模擬器 — 程式進入點

啟動 PyQt6 GUI 應用程式。
"""

import sys
import os

# 確保專案根目錄在 Python path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ui.app import SimulatorApp


def main():
    """程式進入點"""
    print("=" * 50)
    print("  iGPS 無線電傳播模擬器")
    print("  Terrain-based Radio Propagation Simulator")
    print("=" * 50)
    print("正在載入 DEM 資料與初始化模組...")

    app = QApplication(sys.argv)

    window = SimulatorApp()
    window.show()

    print("啟動完成！")
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
