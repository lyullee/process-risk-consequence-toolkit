# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Public fire screening equations; no proprietary fuel or flame-shape tables.

NOAA NOS OR&R 43 (2013), sections 6.1, 6.3.2 and 6.3.4.
"""
import math
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import Model, Name, Nonnegative, Positive, Probability


class FireballInput(Model):
    participating_mass_kg: Annotated[float, Field(gt=0, le=5_000_000)]
    mass_basis: Name
    correlation: Literal["noaa_2013_roberts_diameter_dutch_duration"]


class FireballOutput(Model):
    diameter_m: Positive
    duration_s: Positive


def fireball(x: FireballInput) -> FireballOutput:
    # SI-specific empirical coefficients; participating mass is not inferred.
    return FireballOutput(diameter_m=5.8 * math.cbrt(x.participating_mass_kg),
                          duration_s=.852 * x.participating_mass_kg ** .26)


class SolidFlameInput(Model):
    surface_emissive_power_w_m2: Nonnegative
    view_factor: Probability
    transmissivity: Probability
    emissive_power_basis: Name
    view_factor_basis: Name
    applicability: Literal["supplied_solid_flame_geometry"]


class FluxOutput(Model):
    heat_flux_w_m2: Nonnegative


def solid_flame(x: SolidFlameInput) -> FluxOutput:
    return FluxOutput(heat_flux_w_m2=x.surface_emissive_power_w_m2 * x.view_factor * x.transmissivity)


class SphereInput(Model):
    diameter_m: Positive
    horizontal_distance_m: Positive
    surface_emissive_power_w_m2: Nonnegative
    transmissivity: Probability
    emissive_power_basis: Name
    geometry: Literal["ground_tangent_sphere_ground_level_vertical_receptor"]

    @model_validator(mode="after")
    def outside(self):
        if self.horizontal_distance_m <= self.diameter_m / 2:
            raise ValueError("sphere correlation requires horizontal distance greater than radius")
        return self


class SphereOutput(Model):
    view_factor: Probability
    heat_flux_w_m2: Nonnegative


def sphere(x: SphereInput) -> SphereOutput:
    # r^2*x/(x^2+r^2)^1.5; ratio form avoids squaring dimensional distances.
    ratio = (x.diameter_m / 2) / x.horizontal_distance_m
    factor = ratio ** 2 / (1 + ratio ** 2) ** 1.5
    return SphereOutput(view_factor=factor,
                        heat_flux_w_m2=x.surface_emissive_power_w_m2 * factor * x.transmissivity)


class PoolInput(Model):
    area_m2: Positive
    burning_flux_kg_m2_s: Nonnegative
    inventory_kg: Nonnegative
    duration_s: Nonnegative
    heat_of_combustion_j_kg: Positive
    combustion_efficiency: Probability
    burning_flux_basis: Name
    applicability: Literal["constant_area_constant_burning_flux_no_replenishment"]


class PoolOutput(Model):
    mass_rate_kg_s: Nonnegative
    burned_mass_kg: Nonnegative
    remaining_mass_kg: Nonnegative
    effective_duration_s: Nonnegative
    heat_release_rate_w: Nonnegative
    released_energy_j: Nonnegative


def pool(x: PoolInput) -> PoolOutput:
    rate = x.area_m2 * x.burning_flux_kg_m2_s
    mass = min(x.inventory_kg, rate * x.duration_s)
    active_rate = rate if mass > 0 else 0.
    heat = x.heat_of_combustion_j_kg * x.combustion_efficiency
    return PoolOutput(mass_rate_kg_s=active_rate, burned_mass_kg=mass,
                      remaining_mass_kg=x.inventory_kg - mass,
                      effective_duration_s=mass / rate if rate else 0.,
                      heat_release_rate_w=active_rate * heat, released_energy_j=mass * heat)
