# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Passive open-terrain Gaussian kernels; sigma values must be supplied."""
import math
from typing import Literal
from .contracts import Model, Positive, Nonnegative, Name


class PlumeInput(Model):
    mass_rate_kg_s: Nonnegative
    wind_speed_m_s: Positive
    downwind_distance_m: Positive
    crosswind_distance_m: float
    receptor_height_m: Nonnegative
    release_height_m: Nonnegative
    sigma_y_m: Positive
    sigma_z_m: Positive
    sigma_basis: Name
    applicability: Literal["passive_steady_open_terrain"]


class ConcentrationOutput(Model):
    concentration_kg_m3: Nonnegative


def plume(x: PlumeInput) -> ConcentrationOutput:
    vertical = math.exp(-.5 * ((x.receptor_height_m - x.release_height_m) / x.sigma_z_m) ** 2)
    vertical += math.exp(-.5 * ((x.receptor_height_m + x.release_height_m) / x.sigma_z_m) ** 2)
    c = x.mass_rate_kg_s / (2 * math.pi * x.wind_speed_m_s * x.sigma_y_m * x.sigma_z_m)
    c *= math.exp(-.5 * (x.crosswind_distance_m / x.sigma_y_m) ** 2) * vertical
    return ConcentrationOutput(concentration_kg_m3=c)


class PuffInput(Model):
    mass_kg: Nonnegative
    downwind_distance_m: float
    crosswind_distance_m: float
    receptor_height_m: Nonnegative
    release_height_m: Nonnegative
    wind_speed_m_s: Positive
    elapsed_s: Positive
    sigma_x_m: Positive
    sigma_y_m: Positive
    sigma_z_m: Positive
    sigma_basis: Name
    applicability: Literal["passive_instantaneous_open_terrain"]


def puff(x: PuffInput) -> ConcentrationOutput:
    vertical = math.exp(-.5 * ((x.receptor_height_m - x.release_height_m) / x.sigma_z_m) ** 2)
    vertical += math.exp(-.5 * ((x.receptor_height_m + x.release_height_m) / x.sigma_z_m) ** 2)
    c = x.mass_kg / ((2 * math.pi) ** 1.5 * x.sigma_x_m * x.sigma_y_m * x.sigma_z_m)
    c *= math.exp(-.5 * ((x.downwind_distance_m - x.wind_speed_m_s * x.elapsed_s) / x.sigma_x_m) ** 2)
    c *= math.exp(-.5 * (x.crosswind_distance_m / x.sigma_y_m) ** 2) * vertical
    return ConcentrationOutput(concentration_kg_m3=c)


class RichardsonInput(Model):
    cloud_density_kg_m3: Positive
    air_density_kg_m3: Positive
    characteristic_dimension_m: Positive
    friction_velocity_m_s: Positive
    gravity_m_s2: Positive
    characteristic_dimension_basis: Name
    applicability: Literal["noaa_2013_friction_richardson_screen"]


class RichardsonOutput(Model):
    reduced_gravity_m_s2: float
    friction_richardson_number: float
    screening: Literal["passive_candidate", "dense_model_required", "buoyant_review_required"]
    concentration_prediction_available: Literal[False] = False


def richardson(x: RichardsonInput) -> RichardsonOutput:
    reduced = x.gravity_m_s2 * (x.cloud_density_kg_m3 - x.air_density_kg_m3) / x.air_density_kg_m3
    number = reduced * x.characteristic_dimension_m / x.friction_velocity_m_s ** 2
    if reduced < 0:
        status = "buoyant_review_required"
    else:
        status = "passive_candidate" if number < 1 else "dense_model_required"
    return RichardsonOutput(reduced_gravity_m_s2=reduced, friction_richardson_number=number, screening=status)
