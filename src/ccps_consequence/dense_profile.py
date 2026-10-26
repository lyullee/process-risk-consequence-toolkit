# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Independently authored normalized SLAB Eq.28 puff similarity kernel.

Only spatial reconstruction is here. Dense-cloud dynamics are solved by the
separately installed engine. A moving peak is not a fixed-receptor history.
"""
import math


def horizontal_shape(coordinate, half_shape, gaussian_width):
    if half_shape <= 0 or gaussian_width <= 0:
        raise ValueError("positive puff shape widths required")
    lo = (coordinate - half_shape) / (math.sqrt(2) * gaussian_width)
    hi = (coordinate + half_shape) / (math.sqrt(2) * gaussian_width)
    if lo >= 0:
        return math.erfc(lo) - math.erfc(hi)
    if hi <= 0:
        return math.erfc(-hi) - math.erfc(-lo)
    return math.erf(hi) - math.erf(lo)


def normalized_profile(*, dx, y, z, center_z, bx, by, beta_x, beta_y, sigma_z):
    if z < 0 or center_z < 0 or sigma_z <= 0:
        raise ValueError("invalid vertical puff geometry")
    horizontal = horizontal_shape(dx, bx, beta_x) * horizontal_shape(y, by, beta_y)
    vertical = math.exp(-.5 * ((z-center_z)/sigma_z)**2) + math.exp(-.5 * ((z+center_z)/sigma_z)**2)
    # Horizontal integrals are 4*b; ground-reflected vertical integral is sqrt(2*pi)*sigma.
    return horizontal * vertical / (16 * bx * by * math.sqrt(2*math.pi) * sigma_z)
