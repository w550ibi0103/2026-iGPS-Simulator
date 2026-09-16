# -*- coding: utf-8 -*-
"""
DEM 載入模組

負責讀取 GeoTIFF 格式的數位高程模型 (DEM) 檔案，
提供單點海拔查詢功能。使用 rasterio 處理柵格資料。
"""

import numpy as np
import rasterio
from rasterio.transform import rowcol

from config import NO_DATA_VALUE, SEA_LEVEL_ELEVATION


class DEMLoader:
    """
    DEM (Digital Elevation Model) 檔案載入器

    使用 rasterio 讀取 GeoTIFF 格式的 DEM 檔案，
    提供海拔查詢與 CRS / Transform 資訊存取。
    """

    def __init__(self, dem_path: str):
        """
        載入 DEM 檔案

        Parameters
        ----------
        dem_path : str
            DEM GeoTIFF 檔案的完整路徑
        """
        self._dataset = None
        self._dataset = rasterio.open(dem_path)
        # 預先讀取 band 1 到記憶體以加速後續查詢
        self._elevation_data = self._dataset.read(1)
        self._transform = self._dataset.transform
        self._crs = self._dataset.crs
        self._bounds = self._dataset.bounds
        self._height = self._dataset.height
        self._width = self._dataset.width

    def get_elevation(self, x_twd97: float, y_twd97: float) -> float:
        """
        查詢指定 TWD97 TM2 座標的海拔高度

        若座標在海上 (DEM 值為 NO_DATA_VALUE = -32767)，
        則自動回傳 0 (海平面)。

        Parameters
        ----------
        x_twd97 : float
            TWD97 TM2 的 Easting (X) 座標 (公尺)
        y_twd97 : float
            TWD97 TM2 的 Northing (Y) 座標 (公尺)

        Returns
        -------
        float
            海拔高度 (公尺)，海上區域回傳 0
        """
        try:
            # 將 TWD97 座標轉為像素 row, col
            row, col = rowcol(self._transform, x_twd97, y_twd97)

            # 邊界檢查
            if row < 0 or row >= self._height or col < 0 or col >= self._width:
                return SEA_LEVEL_ELEVATION

            elevation = float(self._elevation_data[row, col])

            # 海上區域 (NO_DATA) 替換為 0
            if elevation <= NO_DATA_VALUE:
                return SEA_LEVEL_ELEVATION

            return elevation

        except Exception:
            return SEA_LEVEL_ELEVATION

    def get_elevations_batch(self, coords: list) -> np.ndarray:
        """
        批次查詢多個 TWD97 TM2 座標的海拔高度

        Parameters
        ----------
        coords : list of tuple
            TWD97 座標列表，每個元素為 (x, y)

        Returns
        -------
        np.ndarray
            海拔高度陣列
        """
        elevations = np.zeros(len(coords))
        for i, (x, y) in enumerate(coords):
            elevations[i] = self.get_elevation(x, y)
        return elevations

    def get_transform(self):
        """取得 DEM 的 affine transform"""
        return self._transform

    def get_crs(self):
        """取得 DEM 的座標參考系統"""
        return self._crs

    def get_bounds(self):
        """取得 DEM 的空間範圍"""
        return self._bounds

    def close(self):
        """關閉 DEM 檔案"""
        if self._dataset:
            self._dataset.close()

    def __del__(self):
        """解構子：確保檔案被關閉"""
        self.close()
