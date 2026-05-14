# -*- coding: utf-8 -*-
"""
剖面圖繪製模組

使用 matplotlib 繪製兩站基地台之間的地形剖面圖。

繪圖策略（等效平面地球法）：
  - 地形：顯示曲率校正後的海拔（地形隆起）
  - LOS：直線
  - 這是無線電工程中的標準呈現方式
"""

import numpy as np
from matplotlib.figure import Figure

from core.terrain_profile import TerrainProfile
from core.los_analysis import LOSResult
from core.fresnel import FresnelResult


class ProfilePlotter:
    """地形剖面圖繪製器（等效平面地球法）"""

    COLOR_TERRAIN = '#8B7355'
    COLOR_TERRAIN_EDGE = '#5C4033'
    COLOR_LOS_CLEAR = '#2ECC71'
    COLOR_LOS_BLOCKED = '#E74C3C'
    COLOR_FRESNEL = '#3498DB'
    COLOR_OBSTRUCTION = '#E74C3C'
    COLOR_ANTENNA = '#E67E22'
    COLOR_SKY = '#D6EAF8'

    def plot(self, fig: Figure,
             profile: TerrainProfile,
             los_result: LOSResult,
             fresnel_result: FresnelResult,
             h_ant1: float, h_ant2: float):
        """在指定的 Figure 上繪製剖面圖（等效平面地球法）"""
        fig.clear()
        ax = fig.add_subplot(111)

        distances_km = profile.distances / 1000.0

        # 1. 天空背景
        ax.set_facecolor(self.COLOR_SKY)

        # 2. 地形剖面 (含曲率校正，填充)
        ax.fill_between(
            distances_km, los_result.terrain_corrected,
            alpha=0.7, color=self.COLOR_TERRAIN,
            label='地形 (含曲率校正)'
        )
        ax.plot(distances_km, los_result.terrain_corrected,
                color=self.COLOR_TERRAIN_EDGE, linewidth=1.0)

        # 3. LOS 視線直線
        los_color = self.COLOR_LOS_CLEAR if los_result.is_clear \
            else self.COLOR_LOS_BLOCKED
        los_label = 'LOS (暢通)' if los_result.is_clear else 'LOS (遮蔽)'
        ax.plot(distances_km, los_result.los_heights,
                color=los_color, linewidth=2.0, label=los_label)

        # 4. 第一菲涅爾區邊界 (虛線)
        ax.plot(distances_km, fresnel_result.fresnel_upper,
                color=self.COLOR_FRESNEL, linewidth=1.0,
                linestyle='--', alpha=0.6, label='1st Fresnel Zone')
        ax.plot(distances_km, fresnel_result.fresnel_lower,
                color=self.COLOR_FRESNEL, linewidth=1.0,
                linestyle='--', alpha=0.6)

        # 5. 標記遮蔽區域
        if los_result.obstruction_indices:
            for j in los_result.obstruction_indices:
                ax.vlines(distances_km[j],
                          los_result.los_heights[j],
                          los_result.terrain_corrected[j],
                          color=self.COLOR_OBSTRUCTION, alpha=0.3, linewidth=1)

        # 6. 標注兩站天線位置
        ant1_h = los_result.terrain_corrected[0] + h_ant1
        ax.plot(distances_km[0], ant1_h, marker='^',
                color=self.COLOR_ANTENNA, markersize=12, zorder=5)
        ax.annotate(
            f'站A\n海拔:{los_result.terrain_corrected[0]:.0f}m\n'
            f'天線高:{h_ant1:.0f}m',
            xy=(distances_km[0], ant1_h), xytext=(15, 15),
            textcoords='offset points', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.8),
            arrowprops=dict(arrowstyle='->', color='gray'),
            fontfamily='Microsoft JhengHei')

        ant2_h = los_result.terrain_corrected[-1] + h_ant2
        ax.plot(distances_km[-1], ant2_h, marker='^',
                color=self.COLOR_ANTENNA, markersize=12, zorder=5)
        ax.annotate(
            f'站B\n海拔:{los_result.terrain_corrected[-1]:.0f}m\n'
            f'天線高:{h_ant2:.0f}m',
            xy=(distances_km[-1], ant2_h), xytext=(-15, 15),
            textcoords='offset points', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.8),
            arrowprops=dict(arrowstyle='->', color='gray'),
            ha='right', fontfamily='Microsoft JhengHei')

        # 7. 軸標籤
        ax.set_xlabel('距離 (km)', fontsize=10,
                       fontfamily='Microsoft JhengHei')
        ax.set_ylabel('海拔 (m)', fontsize=10,
                       fontfamily='Microsoft JhengHei')
        ax.set_title('地形剖面圖 (等效平面地球法, k=4/3)', fontsize=12,
                      fontweight='bold', fontfamily='Microsoft JhengHei')
        ax.legend(loc='upper right', fontsize=8,
                  prop={'family': 'Microsoft JhengHei'})
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
