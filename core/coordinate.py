# -*- coding: utf-8 -*-
"""
座標轉換模組

提供 WGS84 (EPSG:4326) 與 TWD97 TM2 (EPSG:3826) 之間的座標互轉。
使用 pyproj.Transformer 進行高精度轉換。
"""

from pyproj import Transformer

from config import EPSG_WGS84, EPSG_TWD97_TM2


class CoordinateConverter:
    """
    座標轉換器

    封裝 WGS84 經緯度 ↔ TWD97 TM2 投影座標的雙向轉換。
    使用 always_xy=True 確保座標順序為 (x, y) / (lon, lat)。
    """

    def __init__(self):
        """初始化雙向 Transformer"""
        # WGS84 → TWD97 TM2
        self._to_twd97 = Transformer.from_crs(
            EPSG_WGS84, EPSG_TWD97_TM2, always_xy=True
        )
        # TWD97 TM2 → WGS84
        self._to_wgs84 = Transformer.from_crs(
            EPSG_TWD97_TM2, EPSG_WGS84, always_xy=True
        )

    def wgs84_to_twd97(self, lon: float, lat: float) -> tuple:
        """
        WGS84 經緯度 → TWD97 TM2 投影座標

        Parameters
        ----------
        lon : float
            經度 (度)
        lat : float
            緯度 (度)

        Returns
        -------
        tuple of (float, float)
            (easting_x, northing_y) 單位：公尺
        """
        x, y = self._to_twd97.transform(lon, lat)
        return x, y

    def twd97_to_wgs84(self, x: float, y: float) -> tuple:
        """
        TWD97 TM2 投影座標 → WGS84 經緯度

        Parameters
        ----------
        x : float
            Easting (公尺)
        y : float
            Northing (公尺)

        Returns
        -------
        tuple of (float, float)
            (longitude, latitude) 單位：度
        """
        lon, lat = self._to_wgs84.transform(x, y)
        return lon, lat
