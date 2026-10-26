# Complete module reference

Generated from the 23 actual Python input/output contracts; regenerate, do not edit field tables by hand.
Nested types are documented in [shared models](REFERENCE_MODELS.md). SI suffixes are authoritative; schema carries exact enums/bounds.

| ID | Input model | Output model | Execution |
|---|---|---|---|
| [source/liquid](modules/source__liquid.md) | `LiquidInput` | `RateOutput` | `native_primitive` |
| [source/gas](modules/source__gas.md) | `GasInput` | `RateOutput` | `native_primitive` |
| [source/inventory](modules/source__inventory.md) | `InventoryInput` | `InventoryOutput` | `native_primitive` |
| [source/flash](modules/source__flash.md) | `FlashInput` | `FlashOutput` | `native_primitive` |
| [source/evaporation](modules/source__evaporation.md) | `EvaporationInput` | `InventoryOutput` | `native_primitive` |
| [dispersion/plume](modules/dispersion__plume.md) | `PlumeInput` | `ConcentrationOutput` | `native_primitive` |
| [dispersion/puff](modules/dispersion__puff.md) | `PuffInput` | `ConcentrationOutput` | `native_primitive` |
| [effects/radiation](modules/effects__radiation.md) | `RadiationInput` | `RadiationOutput` | `native_primitive` |
| [effects/dose](modules/effects__dose.md) | `DoseInput` | `DoseOutput` | `native_primitive` |
| [effects/probit](modules/effects__probit.md) | `ProbitInput` | `ProbitOutput` | `native_primitive` |
| [effects/tnt-scaling](modules/effects__tnt-scaling.md) | `TntInput` | `TntOutput` | `native_primitive` |
| [effects/threshold](modules/effects__threshold.md) | `ThresholdInput` | `ThresholdOutput` | `native_primitive` |
| [risk/conditional](modules/risk__conditional.md) | `RiskInput` | `RiskOutput` | `native_primitive` |
| [dispersion/richardson-screen](modules/dispersion__richardson-screen.md) | `RichardsonInput` | `RichardsonOutput` | `native_primitive` |
| [fire/fireball](modules/fire__fireball.md) | `FireballInput` | `FireballOutput` | `native_primitive` |
| [fire/solid-flame](modules/fire__solid-flame.md) | `SolidFlameInput` | `FluxOutput` | `native_primitive` |
| [fire/sphere-radiation](modules/fire__sphere-radiation.md) | `SphereInput` | `SphereOutput` | `native_primitive` |
| [fire/pool-energy](modules/fire__pool-energy.md) | `PoolInput` | `PoolOutput` | `native_primitive` |
| [explosion/epa-1psi](modules/explosion__epa-1psi.md) | `EpaOnePsiInput` | `EpaOnePsiOutput` | `native_primitive` |
| [dispersion/slabx-instantaneous](modules/dispersion__slabx-instantaneous.md) | `DenseInput` | `DenseOutput` | `optional_slabx_worker` |
| [dispersion/history-dose](modules/dispersion__history-dose.md) | `HistoryDoseInput` | `HistoryDoseOutput` | `native_primitive` |
| [dispersion/slabx-release-history](modules/dispersion__slabx-release-history.md) | `ReleaseHistoryInput` | `ReleaseHistoryOutput` | `optional_slabx_worker` |
| [dispersion/coupled-layer-1d](modules/dispersion__coupled-layer-1d.md) | `CoupledInput` | `CoupledOutput` | `coupled_research` |

Other public infrastructure: `contracts`, `catalog`, `api`, `workflow`, `integrations`, optional `pha_adapter`, `cli`, `http_api`; see [manual](MANUAL.md) and [integration contracts](INTEGRATIONS.md).
