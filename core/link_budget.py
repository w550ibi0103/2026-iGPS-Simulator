# -*- coding: utf-8 -*-
"""
鏈路預算 (Link Budget) 計算模組

提供自由空間路徑損耗 (FSPL) 與接收功率計算。
考慮的效應：FSPL + Terrain Diffraction Loss
"""

from dataclasses import dataclass

import numpy as np

from config import FREQUENCY_MHZ


@dataclass
class LinkBudgetResult:
    """鏈路預算計算結果"""
    fspl_db: float
    diffraction_loss_db: float
    total_path_loss_db: float
    rx_power_dbm: float


class LinkBudgetCalculator:
    """鏈路預算計算器"""

    def __init__(self, frequency_mhz: float = FREQUENCY_MHZ):
        self._frequency_mhz = frequency_mhz

    @property
    def frequency_mhz(self) -> float:
        return self._frequency_mhz

    def free_space_path_loss(self, distance_m: float) -> float:
        """
        FSPL(dB) = 20·log10(d_km) + 20·log10(f_MHz) + 32.44
        """
        distance_km = distance_m / 1000.0
        if distance_km <= 0:
            return 0.0
        return (20.0 * np.log10(distance_km) +
                20.0 * np.log10(self._frequency_mhz) +
                32.44)

    def received_power(self, tx_power_dbm: float, tx_gain_dbi: float,
                       rx_gain_dbi: float, distance_m: float,
                       diffraction_loss_db: float) -> LinkBudgetResult:
        """
        Prx = Ptx + Gtx + Grx - FSPL - DiffractionLoss
        """
        fspl = self.free_space_path_loss(distance_m)
        total_loss = fspl + diffraction_loss_db
        rx_power = tx_power_dbm + tx_gain_dbi + rx_gain_dbi - total_loss

        return LinkBudgetResult(
            fspl_db=round(fspl, 2),
            diffraction_loss_db=round(diffraction_loss_db, 2),
            total_path_loss_db=round(total_loss, 2),
            rx_power_dbm=round(rx_power, 2),
        )
