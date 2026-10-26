# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""EPA 1999 Appendix C.1 equation C-1: fixed 1 psi screening endpoint only."""
import math
from typing import Literal
from .contracts import Model, Name, Nonnegative, Positive


class EpaOnePsiInput(Model):
    flammable_mass_kg: Nonnegative
    heat_of_combustion_j_kg: Positive
    mass_basis: Name
    applicability: Literal["epa_1999_worst_case_vapour_cloud_1psi"]


class EpaOnePsiOutput(Model):
    equivalent_tnt_mass_kg: Nonnegative
    endpoint_distance_m: Nonnegative
    endpoint_pressure_pa: Literal[6894.757293168] = 6894.757293168
    explosion_efficiency: Literal[0.1] = .1
    tnt_specific_energy_j_kg: Literal[4680000.0] = 4_680_000.


def epa_one_psi(x: EpaOnePsiInput) -> EpaOnePsiOutput:
    mass = .1 * x.flammable_mass_kg * x.heat_of_combustion_j_kg / 4_680_000.
    return EpaOnePsiOutput(equivalent_tnt_mass_kg=mass, endpoint_distance_m=17. * math.cbrt(mass))
