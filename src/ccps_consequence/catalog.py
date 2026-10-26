# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""One source of truth for dispatch, schemas and section/test traceability."""
from dataclasses import dataclass
from typing import Callable
from .contracts import Model
from . import source, dispersion, effects, risk, fire, explosion, dense, release_history, coupled

NOAA = "https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf"
EPA = "https://www.epa.gov/sites/default/files/2017-05/documents/oca-apds.pdf"


@dataclass(frozen=True)
class Calculation:
    input_type: type[Model]
    output_type: type[Model]
    function: Callable
    section: str
    limitation: str
    test: str
    method_references: tuple[str, ...] = ()
    test_file: str = "tests/test_ccps_physics.py"
    execution_kind: str = "native_primitive"


CALCULATIONS = {
    "source/liquid": Calculation(source.LiquidInput, source.RateOutput, source.liquid, "2.1",
        "Nonflashing incompressible orifice only; no pipe friction, hydrostatic head or transient depletion.", "test_liquid_and_inventory"),
    "source/gas": Calculation(source.GasInput, source.RateOutput, source.gas, "2.1",
        "Ideal gas, fixed stagnation state, short orifice; no real gas, two-phase or pipe model.", "test_gas_regimes_and_continuity"),
    "source/inventory": Calculation(source.InventoryInput, source.InventoryOutput, source.inventory, "2.1",
        "Constant rate clipped to inventory; not a transient pressure or replenishment model.", "test_liquid_and_inventory"),
    "source/flash": Calculation(source.FlashInput, source.FlashOutput, source.flash, "2.2",
        "Constant-property sensible-heat approximation; no EOS, aerosol entrainment or two-phase flow.", "test_flash_and_evaporation_mass_balance"),
    "source/evaporation": Calculation(source.EvaporationInput, source.InventoryOutput, source.evaporation, "2.2",
        "User-supplied constant mass flux; no pool energy balance or spreading correlation.", "test_flash_and_evaporation_mass_balance"),
    "dispersion/plume": Calculation(dispersion.PlumeInput, dispersion.ConcentrationOutput, dispersion.plume, "2.3.1",
        "Passive steady open terrain with ground reflection; user owns sigma/distance consistency; no dense gas, buildings or finite-duration front.", "test_gaussian_identities"),
    "dispersion/puff": Calculation(dispersion.PuffInput, dispersion.ConcentrationOutput, dispersion.puff, "2.3.1",
        "Passive instantaneous puff with ground reflection; supplied sigmas; no dense gas or deposition.", "test_gaussian_identities"),
    "effects/radiation": Calculation(effects.RadiationInput, effects.RadiationOutput, effects.radiation, "3.6,3.7,4.3",
        "Far-field point-source screening only; no flame geometry, jet trajectory or near-field prediction.", "test_radiation_inverse_square"),
    "effects/dose": Calculation(effects.DoseInput, effects.DoseOutput, effects.dose, "4.1,4.2,4.3",
        "Piecewise-constant normalized exposure; coefficients must use the same concentration/flux and time reference.", "test_dose_and_probit"),
    "effects/probit": Calculation(effects.ProbitInput, effects.ProbitOutput, effects.probit, "4.1",
        "User-supplied dimensionless-log convention and coefficients; no toxicity database or endpoint certification.", "test_dose_and_probit"),
    "effects/tnt-scaling": Calculation(effects.TntInput, effects.TntOutput, effects.tnt, "3.1",
        "Energy equivalence and scaled distance only; no blast pressure curve, congestion, confinement or impulse.", "test_tnt_and_threshold"),
    "effects/threshold": Calculation(effects.ThresholdInput, effects.ThresholdOutput, effects.threshold, "4.2,4.3,4.4",
        "Single receptor threshold comparison; not a contour, fatality probability or exposure-duration criterion.", "test_tnt_and_threshold"),
    "risk/conditional": Calculation(risk.RiskInput, risk.RiskOutput, risk.risk, "1.2",
        "One LOC scenario, one receptor and explicit branch partition; no facility total or dependence inference.", "test_risk_ownership_and_partition"),
    "dispersion/richardson-screen": Calculation(dispersion.RichardsonInput, dispersion.RichardsonOutput, dispersion.richardson, "2.3.2",
        "Friction Richardson diagnostic only; supplied characteristic dimension and friction velocity; no concentration solver or automatic Gaussian routing.",
        "test_richardson_screen", (NOAA + "#page=54", NOAA + "#page=55")),
    "fire/fireball": Calculation(fire.FireballInput, fire.FireballOutput, fire.fireball, "3.4",
        "Public empirical size/duration only; caller supplies participating mass; 0 < mass <= 5e6 kg; no rupture, flash fraction, lift-off or pressurized-gas applicability claim.",
        "test_fireball_public_correlations", (NOAA + "#page=75", NOAA + "#page=76", NOAA + "#page=77")),
    "fire/solid-flame": Calculation(fire.SolidFlameInput, fire.FluxOutput, fire.solid_flame, "3.4,3.6,3.7,4.3",
        "Supplied emissive power, view factor and transmissivity only; no pool/jet flame geometry or fuel database.",
        "test_solid_flame_bounds", (NOAA + "#page=73",)),
    "fire/sphere-radiation": Calculation(fire.SphereInput, fire.SphereOutput, fire.sphere, "3.4,4.3",
        "Ground-tangent sphere and ground-level facing vertical receptor, horizontal distance > radius only; no shielding, lift-off or automatic emissive power.",
        "test_sphere_radiation_geometry", (NOAA + "#page=77",)),
    "fire/pool-energy": Calculation(fire.PoolInput, fire.PoolOutput, fire.pool, "3.6",
        "Conservation wrapper with supplied burning flux, constant area and no replenishment; active HRR not an interval average; no burning-flux or flame-height correlation.",
        "test_pool_energy_balance", (NOAA + "#page=73", "Conservation of mass and energy; independently authored finite-inventory wrapper")),
    "explosion/epa-1psi": Calculation(explosion.EpaOnePsiInput, explosion.EpaOnePsiOutput, explosion.epa_one_psi, "3.1,4.4",
        "EPA 1999 C-1 worst-case screening: fixed 10% yield, 4.68 MJ/kg TNT energy, 1 psi endpoint only; not an arbitrary-pressure curve, confinement model or regulatory compliance determination.",
        "test_epa_one_psi_endpoint", (EPA + "#page=19",)),
    "dispersion/slabx-instantaneous": Calculation(dense.DenseInput, dense.DenseOutput, dense.run_dense, "2.3.2,4.2",
        "Optional pinned SLABx 1.0.8, instantaneous dense pure vapour at ground level only; flat terrain, no meander. Reconstructed ensemble histories, sampled peaks/integrals and finite-window tail diagnostics; no continuous source, droplets, LH2 correction or field validation.",
        "test_real_dense_history", ("https://www.epa.gov/scram/air-quality-dispersion-modeling-alternative-models#slab",
        "https://github.com/lyullee/slabx", "Ermak 1990 UCRL-MA-105607 sections 2.3.2 and 2.4, equations 15-28; normalized similarity reconstruction"),
        "tests/test_ccps_dense.py", "optional_slabx_worker"),
    "dispersion/history-dose": Calculation(dense.HistoryDoseInput, dense.HistoryDoseOutput, dense.integrate_history, "4.1,4.2",
        "Trapezoid quadrature of powered sampled concentrations over the supplied window only; no tail extrapolation, toxicity coefficients or exact unsampled peak/integral claim.",
        "test_history_dose_trapezoid", ("Independent trapezoid quadrature; normalized exposure integral",), "tests/test_ccps_dense.py"),
    "dispersion/slabx-release-history": Calculation(release_history.ReleaseHistoryInput, release_history.ReleaseHistoryOutput, release_history.run_release_history, "2.3.2,4.2",
        "Pinned SLABx constant ground-vapour segments; finite plume-to-puff and continuous-through-window modes. Pretransition growing-cloud reconstruction and independent segment superposition are explicit approximations, not a coupled arbitrary-rate solver. No jet momentum, droplets, LH2 corrections or cloud interaction.",
        "test_real_finite_plume_to_puff", ("https://www.epa.gov/scram/air-quality-dispersion-modeling-alternative-models#slab",
        "https://github.com/lyullee/slabx", "Ermak 1990 equations 29-30; own mass-normalized quasi-steady pretransition closure"),
        "tests/test_ccps_release_history.py", "optional_slabx_worker"),
    "dispersion/coupled-layer-1d": Calculation(coupled.CoupledInput,coupled.CoupledOutput,coupled.solve_coupled,"2.3.2,4.2",
        "Research 1D isothermal fixed-width vertically mixed layer: shared mixture/species/momentum finite-volume field with composition-dependent hydrostatic pressure. User-qualified densities, entrainment and wind relaxation; no energy equation, 2D spreading, obstacles, droplets or field validation. Not a SLAB/TWODEE implementation.",
        "test_coupled_mass_and_interaction",("https://doi.org/10.1029/2007GC001762","https://arxiv.org/abs/2101.04384",
        "https://www.clawpack.org/v5.12.x/riemann/Shallow_water_Riemann_solvers.html",
        "Own isothermal additive-volume closure, reduced hydrostatic pressure and first-order Rusanov implementation"),"tests/test_ccps_coupled.py","coupled_research"),
}

DEFERRED = {
    "2.3.2": "slabx_and_research_1d_coupled_available_2d_nonisothermal_models_external",
    "3.2": "flash_fire_geometry_external_provider",
    "3.3": "physical_explosion_external_provider",
    "3.4": "bleve_rupture_and_full_fireball_dynamics_external_provider_partial_geometry_native",
    "3.5": "confined_explosion_external_provider",
    "5": "evacuation_external_provider",
    "6": "external_model_system_boundary",
}

PUBLIC_REFERENCE = "https://repository.library.noaa.gov/view/noaa/2669"


def calculation_catalog():
    return [{"calculation_id": key, "python_path": f"ccps_consequence.{c.function.__module__.rsplit('.', 1)[-1]}.{c.function.__name__}",
             "sections": c.section.split(","), "coverage": "restricted_research_1d" if c.execution_kind=="coupled_research" else "public_primitive_partial",
             "method_origin": "authored_restricted_research_pde" if c.execution_kind=="coupled_research" else "optional_slabx_and_authored_reconstruction" if c.execution_kind == "optional_slabx_worker" else "independently_authored_public_physics",
             "execution_kind": c.execution_kind,
             "limitations": [c.limitation], "test": f"{c.test_file}::{c.test}",
             "public_context_reference": PUBLIC_REFERENCE,
             "method_references": list(c.method_references),
             "validation_evidence": {"kind": "synthetic_numerical_conservation_convergence" if c.execution_kind=="coupled_research" else "synthetic_real_engine_and_analytic" if c.execution_kind == "optional_slabx_worker" else "synthetic_analytic", "external_evaluation": False}}
            for key, c in CALCULATIONS.items()]


def contract_schemas():
    from .contracts import Receipt, Context
    from .workflow import Workflow, WorkflowResult
    from .integrations import ExternalSource, ProviderRequest, ProviderResult
    return {"schema_version": "ccps.contracts.v1", "calculations": {
        key: {"input": c.input_type.model_json_schema(), "output": c.output_type.model_json_schema()}
        for key, c in CALCULATIONS.items()}, "receipt": Receipt.model_json_schema(),
        "context": Context.model_json_schema(), "workflow": Workflow.model_json_schema(),
        "workflow_result": WorkflowResult.model_json_schema(),
        "frequency": risk.Frequency.model_json_schema(),
        "external_source": ExternalSource.model_json_schema(),
        "provider_request": ProviderRequest.model_json_schema(), "provider_result": ProviderResult.model_json_schema(),
        "instantaneous_source": dense.DenseInventory.model_json_schema(), "dense_request": dense.DenseInput.model_json_schema(),
        "dense_result": dense.DenseOutput.model_json_schema(),
        "release_history_source": release_history.ReleaseHistory.model_json_schema(),
        "release_history_request": release_history.ReleaseHistoryInput.model_json_schema(),
        "release_history_result": release_history.ReleaseHistoryOutput.model_json_schema(),
        "coupled_request": coupled.CoupledInput.model_json_schema(),"coupled_result": coupled.CoupledOutput.model_json_schema()}
