# -*- coding: utf-8 -*-
"""
側向地形掃描圖繪製模組

使用 matplotlib 繪製兩站連線走廊的側向地形掃描結果。
X 軸: 沿線距離 (km)，Y 軸: 側向偏移 (m)，
以像素塊標記地形高度穿越直線 LOS 高度的區域。
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.colors import to_rgba
from matplotlib.patches import Patch

from core.lateral_scan import LateralScanResult


class LateralScanPlotter:
    """側向地形掃描圖繪製器"""

    COLOR_BACKGROUND = '#D6EAF8'
    COLOR_INTRUSION = '#E74C3C'
    COLOR_CENTERLINE = '#2ECC71'

    def plot(self, fig: Figure, scan_result: LateralScanResult):
        """在指定的 Figure 上繪製側向地形掃描圖"""
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.COLOR_BACKGROUND)

        distances_km = scan_result.distances / 1000.0
        offsets = scan_result.offsets
        mask = scan_result.intrusion_mask

        # 以 RGBA 像素塊繪製：無侵入處透明 (露出天空背景)，侵入處填色
        rgba = np.zeros((*mask.shape, 4))
        rgba[mask] = to_rgba(self.COLOR_INTRUSION)
        ax.imshow(rgba, origin='lower', aspect='auto',
                  interpolation='nearest',
                  extent=[distances_km[0], distances_km[-1],
                          offsets[0], offsets[-1]])

        ax.axhline(0, color=self.COLOR_CENTERLINE, linewidth=1.2,
                   linestyle='--')

        # 軸範圍固定為完整掃描範圍
        ax.set_xlim(distances_km[0], distances_km[-1])
        ax.set_ylim(offsets[0], offsets[-1])

        legend_handles = [
            Patch(facecolor=self.COLOR_INTRUSION, label='地形穿越 LOS 高度'),
            Patch(facecolor=self.COLOR_CENTERLINE, label='兩站中心連線'),
        ]
        ax.legend(handles=legend_handles, loc='upper right', fontsize=8,
                  prop={'family': 'Microsoft JhengHei'})

        ax.set_xlabel('距離 (km)', fontsize=10,
                       fontfamily='Microsoft JhengHei')
        ax.set_ylabel('側向偏移 (m)', fontsize=10,
                       fontfamily='Microsoft JhengHei')
        ax.set_title('側向地形掃描圖 (走廊地形是否穿越 LOS 高度)', fontsize=12,
                      fontweight='bold', fontfamily='Microsoft JhengHei')
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
