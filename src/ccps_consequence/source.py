# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Public conservation and orifice primitives, independently authored."""
import math
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .contracts import Model, Positive, Nonnegative, Probability


class LiquidInput(Model):
    area_m2: Positive
    density_kg_m3: Positive
    upstream_pressure_pa_abs: Positive
    downstream_pressure_pa_abs: Positive
    discharge_coefficient: Annotated[float, Field(gt=0, le=1)]
    phase: Literal["incompressible_nonflashing_liquid"]

    @model_validator(mode="after")
    def pressure(self):
        if self.upstream_pressure_pa_abs < self.downstream_pressure_pa_abs:
            raise ValueError("reverse pressure difference is unsupported")
        return self


class RateOutput(Model):
    mass_rate_kg_s: Nonnegative
    regime: str


def liquid(x: LiquidInput) -> RateOutput:
    q = x.discharge_coefficient * x.area_m2 * math.sqrt(
        2 * x.density_kg_m3 * (x.upstream_pressure_pa_abs - x.downstream_pressure_pa_abs))
    return RateOutput(mass_rate_kg_s=q, regime="incompressible")


class GasInput(Model):
    area_m2: Positive
    upstream_pressure_pa_abs: Positive
    downstream_pressure_pa_abs: Positive
    temperature_k: Positive
    specific_gas_constant_j_kg_k: Positive
    heat_capacity_ratio: Annotated[float, Field(gt=1, le=2)]
    discharge_coefficient: Annotated[float, Field(gt=0, le=1)]
    phase: Literal["ideal_gas"]

    @model_validator(mode="after")
    def pressure(self):
        if self.upstream_pressure_pa_abs < self.downstream_pressure_pa_abs:
            raise ValueError("reverse pressure difference is unsupported")
        return self


def gas(x: GasInput) -> RateOutput:
    k = x.heat_capacity_ratio
    ratio = x.downstream_pressure_pa_abs / x.upstream_pressure_pa_abs
    critical = (2 / (k + 1)) ** (k / (k - 1))
    if ratio <= critical:
        factor = k * (2 / (k + 1)) ** ((k + 1) / (k - 1))
        regime = "choked"
    else:
        # expm1 avoids cancellation near equal pressures.
        factor = 2 * k / (k - 1) * ratio ** (2 / k) * (-math.expm1((k - 1) / k * math.log(ratio)))
        regime = "subsonic"
    q = x.discharge_coefficient * x.area_m2 * x.upstream_pressure_pa_abs * math.sqrt(
        factor / (x.specific_gas_constant_j_kg_k * x.temperature_k))
    return RateOutput(mass_rate_kg_s=q, regime=regime)


class InventoryInput(Model):
    mass_rate_kg_s: Nonnegative
    duration_s: Nonnegative
    inventory_kg: Nonnegative


class InventoryOutput(Model):
    released_mass_kg: Nonnegative
    remaining_mass_kg: Nonnegative
    effective_duration_s: Nonnegative


def inventory(x: InventoryInput) -> InventoryOutput:
    mass = min(x.inventory_kg, x.mass_rate_kg_s * x.duration_s)
    return InventoryOutput(released_mass_kg=mass, remaining_mass_kg=x.inventory_kg - mass,
                           effective_duration_s=mass / x.mass_rate_kg_s if x.mass_rate_kg_s else 0.)


class FlashInput(Model):
    mass_kg: Nonnegative
    liquid_heat_capacity_j_kg_k: Positive
    initial_temperature_k: Positive
    boiling_temperature_k: Positive
    latent_heat_j_kg: Positive
    assumption: Literal["constant_properties_sensible_heat_only"]


class FlashOutput(Model):
    vapour_fraction: Probability
    vapour_mass_kg: Nonnegative
    liquid_mass_kg: Nonnegative


def flash(x: FlashInput) -> FlashOutput:
    fraction = min(1., x.liquid_heat_capacity_j_kg_k * max(0., x.initial_temperature_k - x.boiling_temperature_k) / x.latent_heat_j_kg)
    return FlashOutput(vapour_fraction=fraction, vapour_mass_kg=x.mass_kg * fraction,
                       liquid_mass_kg=x.mass_kg * (1 - fraction))


class EvaporationInput(Model):
    area_m2: Positive
    mass_flux_kg_m2_s: Nonnegative
    duration_s: Nonnegative
    inventory_kg: Nonnegative
    flux_basis: Annotated[str, Field(min_length=1)]


def evaporation(x: EvaporationInput) -> InventoryOutput:
    return inventory(InventoryInput(mass_rate_kg_s=x.area_m2 * x.mass_flux_kg_m2_s,
                                    duration_s=x.duration_s, inventory_kg=x.inventory_kg))
