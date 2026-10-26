# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Effects with user-supplied coefficients; no chemical/probit tables."""
import math
from typing import Literal
from pydantic import model_validator
from .contracts import Model, Positive, Nonnegative, Probability, Name


class RadiationInput(Model):
    heat_release_rate_w: Nonnegative
    radiative_fraction: Probability
    transmissivity: Probability
    distance_m: Positive
    applicability: Literal["far_field_isotropic_point_source"]


class RadiationOutput(Model):
    heat_flux_w_m2: Nonnegative


def radiation(x: RadiationInput) -> RadiationOutput:
    return RadiationOutput(heat_flux_w_m2=x.heat_release_rate_w * x.radiative_fraction *
                           x.transmissivity / (4 * math.pi * x.distance_m ** 2))


class DoseInput(Model):
    values: tuple[Nonnegative, ...]
    durations_s: tuple[Positive, ...]
    exponent: Positive
    reference_value: Positive
    reference_unit: Literal["kg/m3", "W/m2", "Pa"]

    @model_validator(mode="after")
    def paired(self):
        if not self.values or len(self.values) != len(self.durations_s):
            raise ValueError("values and durations must be nonempty and paired")
        return self


class DoseOutput(Model):
    normalized_dose_s: Nonnegative


def dose(x: DoseInput) -> DoseOutput:
    return DoseOutput(normalized_dose_s=math.fsum((v / x.reference_value) ** x.exponent * t
                                                 for v, t in zip(x.values, x.durations_s)))


class ProbitInput(Model):
    normalized_dose_s: Nonnegative
    reference_time_s: Positive
    intercept: float
    slope: Positive
    normal_offset: float
    coefficient_basis: Name


class ProbitOutput(Model):
    probability: Probability


def probit(x: ProbitInput) -> ProbitOutput:
    if x.normalized_dose_s == 0:
        return ProbitOutput(probability=0.)
    z = x.intercept + x.slope * math.log(x.normalized_dose_s / x.reference_time_s) - x.normal_offset
    return ProbitOutput(probability=.5 * math.erfc(-z / math.sqrt(2)))


class TntInput(Model):
    flammable_mass_kg: Nonnegative
    heat_of_combustion_j_kg: Positive
    explosion_efficiency: Probability
    tnt_specific_energy_j_kg: Positive
    distance_m: Positive
    efficiency_basis: Name


class TntOutput(Model):
    equivalent_tnt_mass_kg: Nonnegative
    scaled_distance_m_kg_third: Positive | None


def tnt(x: TntInput) -> TntOutput:
    mass = x.flammable_mass_kg * x.heat_of_combustion_j_kg * x.explosion_efficiency / x.tnt_specific_energy_j_kg
    return TntOutput(equivalent_tnt_mass_kg=mass,
                     scaled_distance_m_kg_third=x.distance_m / mass ** (1 / 3) if mass else None)


class ThresholdInput(Model):
    value: Nonnegative
    threshold: Positive
    unit: Literal["kg/m3", "W/m2", "Pa"]
    criterion_basis: Name


class ThresholdOutput(Model):
    exceeded: bool
    ratio: Nonnegative


def threshold(x: ThresholdInput) -> ThresholdOutput:
    return ThresholdOutput(exceeded=x.value >= x.threshold, ratio=x.value / x.threshold)
