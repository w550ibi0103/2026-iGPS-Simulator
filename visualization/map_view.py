# -*- coding: utf-8 -*-
"""
互動地圖模組

使用 folium 建立台灣互動地圖，標示兩站基地台位置、
連線直線，並以顏色區分是否有遮蔽。
"""

import folium


class MapViewer:
    """互動地圖生成器"""

    TAIWAN_CENTER = [23.6978, 120.9605]

    def create_map(self, lat1: float, lon1: float,
                   lat2: float, lon2: float,
                   elev1: float, elev2: float,
                   is_obstructed: bool) -> str:
        """建立互動地圖 HTML"""
        center_lat = (lat1 + lat2) / 2.0
        center_lon = (lon1 + lon2) / 2.0
        zoom = self._calculate_zoom(lat1, lon1, lat2, lon2)

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom, tiles='OpenStreetMap')

        # 站 A 標記
        folium.Marker(
            location=[lat1, lon1],
            popup=folium.Popup(
                f'<b>站 A</b><br>緯度: {lat1:.6f}°<br>'
                f'經度: {lon1:.6f}°<br>海拔: {elev1:.1f} m', max_width=200),
            tooltip='站 A',
            icon=folium.Icon(color='blue', icon='tower-broadcast', prefix='fa'),
        ).add_to(m)

        # 站 B 標記
        folium.Marker(
            location=[lat2, lon2],
            popup=folium.Popup(
                f'<b>站 B</b><br>緯度: {lat2:.6f}°<br>'
                f'經度: {lon2:.6f}°<br>海拔: {elev2:.1f} m', max_width=200),
            tooltip='站 B',
            icon=folium.Icon(color='red', icon='tower-broadcast', prefix='fa'),
        ).add_to(m)

        # 連線
        line_color = 'red' if is_obstructed else 'green'
        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color=line_color, weight=3, opacity=0.8,
            tooltip='遮蔽' if is_obstructed else '暢通',
            dash_array='10' if is_obstructed else None,
        ).add_to(m)

        return m._repr_html_()

    def _calculate_zoom(self, lat1, lon1, lat2, lon2) -> int:
        max_diff = max(abs(lat2 - lat1), abs(lon2 - lon1))
        if max_diff > 2.0: return 7
        elif max_diff > 1.0: return 8
        elif max_diff > 0.5: return 9
        elif max_diff > 0.2: return 10
        elif max_diff > 0.1: return 11
        elif max_diff > 0.05: return 12
        elif max_diff > 0.02: return 13
        elif max_diff > 0.01: return 14
        else: return 15
