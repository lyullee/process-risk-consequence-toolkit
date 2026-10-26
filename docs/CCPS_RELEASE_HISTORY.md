# 연속·유한시간 고밀도 방출 이력

후속 선택지: [연구용 1D 결합 모델](CCPS_COUPLED_LAYER.md)은 하나의 격자에서
상태를 함께 풀며 독립 구간 합산을 사용하지 않습니다. 아래 SLABx 구간 합성
계약은 그대로 유지하고, 두 모델의 가정·범위를 별도로 표시합니다.

`dispersion/slabx-release-history`는 SLABx 1.0.8을 격리 실행하여 일정·변동 유량의
지상 증기 경계를 계산합니다. 유한 구간은 native plume-to-puff 전이 이후 puff를
추적하고, 관측 창 전체에 걸쳐 계속되는 구간은 정상 plume을 보존적으로 채웁니다.
원본 PRISM 이력은 left-held 구간으로 매핑하고 별도 source digest로 보존합니다.

**지원 범위의 핵심:** SLABx의 직접 입력은 일정 유량입니다. 시간변동 이력은
독립적인 일정 유량 구간들의 결과를 합성하는 명시적 근사이며, 구름끼리의
비선형 상호작용을 풀지 않습니다. 유한 방출 전이 이전도 native 정상 plume을
이용한 질량 정규화 성장 구름 근사입니다. 이 부분을 native 임의유량 transient
solver로 표시하지 않습니다. 실제 엔진 실행과 모델의 물리검증은 구분합니다.

## 근거와 소유권

- [EPA의 SLAB 설명·매뉴얼 링크](https://www.epa.gov/scram/air-quality-dispersion-modeling-alternative-models#slab)
- Ermak (1990), UCRL-MA-105607, 식 29–30의 plume/puff 전이와 식 28의 유사분포
- [SLABx 원저장소](https://github.com/lyullee/slabx), 설치 버전 1.0.8의
  `EvaporatingPool`, `run_dispersion`, `transition_state`, `Trajectory` 계약 확인
- 로컬 PRISM `chain_worker`의 left-held `intervals`와 `inventory_source.liquid_jet_rows`
  계약 확인. 원본 endpoint는 다음 구간이 아니므로 중복 적분하지 않음

외부 코드·원문·Fortran·매뉴얼·관측자료는 복사하지 않습니다. 자체 작성한 범위는
입력/출력 계약, PRISM row 매핑, 일정 구간 정규화, 공간 재구성과 합성, ledger 및
테스트입니다. 선택형 SLABx의 기존 버전·라이선스 경계를 유지합니다.

## source 계약과 PRISM 매핑

`ReleaseHistory` (`ccps.release-history.v1`) 필수 항목:

| 항목 | 의미 |
|---|---|
| asset_id / scenario_id / operating_case_id | PHA context와 동일해야 함 |
| origin | prism 또는 user_supplied |
| source_digest / source_code_digest | 원래 이력과 공급자 코드 SHA256 |
| evidence_ids / qualification_basis | 근거 연결과 reduced boundary 적용성 |
| mode | finite 또는 continuous_through_window |
| intervals | start_s, end_s, mass_rate_kg_s; 0에서 시작하고 간격 없이 연결 |
| declared_mass_within_history_kg | sum(rate×interval)와 일치하는 총 질량 |
| area_m2 / temperature_k | 사용자가 자격 확인한 고정 지상 증기 경계 |
| boundary | qualified_ground_level_thermalized_pure_vapour |

실제 0 유량 구간도 명시적으로 입력합니다. 인접한 **동일 유량**은 병합하므로
같은 유량 이력을 더 자주 샘플링했다는 이유로 별도 구름이 만들어지지 않습니다.
최대 128 입력 구간, 병합 후 최대 8개 양의 유량 구간입니다. 원본 입력 digest는
병합하지 않은 이력도 포함합니다.

`history_from_prism_rows(rows, ...)`는 실제 PRISM row 이름인
`time_s`, `total_mass_flow_kg_s`, `gas_mass_flow_kg_s`,
`airborne_liquid_mass_flow_kg_s`, `ground_liquid_mass_flow_kg_s`,
`mass_residual_kg_s`를 읽습니다. 전체 원본 row의 digest를 핀하고, 각 구간의
gas-only 질량분할을 검사합니다. 마지막 row가 duration과 같은 endpoint이면
그 row의 유량을 추가 적분하지 않습니다. endpoint가 없는 left-held row도 마지막
구간을 duration까지 적분합니다. bool·NaN·음수·액적/지면액체·잔차·시간 역전·
해시 불일치는 거부합니다. 실제 PRISM의 다른 필드는 원본 digest에 포함되며
모델에 쓰는 변수로 오인하지 않습니다.

PRISM의 nozzle area·속도·액적·지면 유량을 자동으로 pool 증기 경계로 바꾸지
않습니다. `area_m2`, `temperature_k`, `qualification_basis`는 명시적으로 별도
제공해야 합니다. 순수 증기가 normal boiling temperature에서 지면에 열·운동량
완화되었다는 reduced boundary 적용성은 호출자가 검토해야 합니다.
일반적인 LH2 jet/액적 이력을 이 경계로 직접 통과시키는 기능은 아닙니다.

예제 row는 실제 PRISM 실행 데이터가 아니라 같은 계약에 맞춘 새 합성 입력입니다.
`origin=prism`은 provenance 경로이며 실제 PRISM을 새로 실행했다는 검증 수준을
부여하지 않습니다. upstream source를 다시 계산하거나 유량을 역추정하지 않습니다.

## 추가 요청 항목

기존 DenseAtmosphere, DenseSubstance, DenseReceptor, sample_times_s, timeout,
expected_engine_code_digest를 재사용합니다.

- `applicability="left_held_ground_vapour_release_history"`
- `coupling="independent_constant_segments_no_cloud_interaction"`
- `pretransition_reconstruction="mass_normalized_quasi_steady_growing_cloud"`
- `plume_distance_limit_m`: native plume 격자, 0< x <=100000 m

두 근사 enum은 필수이며 조용히 기본 선택하지 않습니다. finite source는
관측 종료 이전에 멈춰야 합니다. continuous_through_window source는 관측 종료까지
연결되고 마지막 유량이 양수여야 합니다. 이 모드는 무한 총질량을 JSON에 저장하지
않고 **관측 창 안에서의 누적 질량**을 기록합니다.
native x limit가 전이 또는 필요한 clock·수용점을 덮지 못하면 외삽 없이 실패합니다.
source 온도는 normal boiling K와 같아야 하며, source는 대기보다 무거워야 합니다.
방출물 응축·비유한 상태·물리적 체적분율 위반은 실패합니다.

## 전이 이전·이후의 재구성

### 유한 구간

native SLABx가 계산한 mean state와 source clock을 사용합니다. t<T에서 방출물
질량은 q t이고, 이를 전체 성장 구름으로 표현합니다. 전이식 30과 같은 질량
관계를 사용해 `Bx=q t/(4 rho By h mass_fraction)`를 정하고, streamwise shape를
native 전이 초기화와 같은 비율로 구성합니다. 기존 정규화 puff kernel에 이
질량과 증기체적을 곱합니다. source filling의 공간분포를 직접 푸는 것이 아닌
**quasi-steady whole-cloud 근사**입니다. 긴 유한 방출의 source 가까운 정상 농도를
정확히 보존한다고 주장하지 않으며, 그 용도에는 아래 continuous 경로나 별도
결합 transient 모델을 사용해야 합니다.

native 전이점은 q T/2의 적분질량 위치에서 정해지며 source clock T에 일치합니다.
그 위치·시각을 결과에 기록합니다. T 이후는 native puff 상태의 위치·크기·혼합·
밀도 변화를 사용합니다. 전이 전 마지막 성장 구름도 q T로 정규화하므로 전이점의
방출물 질량이 일치합니다. 경계값 T±0.001 s의 농도 연속성을 합성 사례로 시험합니다.

native 전이 cut은 여러 상태를 보간하므로 그 한 점의 steady mass-flux 관계는
작은 잔차가 남을 수 있습니다. `native_transition_flux_relative_residual`에 그대로
기록하고, 보간하지 않은 post-source plume flux 잔차와 구분합니다. cut의 flux를
기계정밀도 보존으로 표시하지 않습니다. puff의 총 방출물 질량은 독립적으로 검사합니다.

### continuous_through_window 구간

정상 plume의 위치별 mean state를 사용하며, 움직이는 성장 구름의 한 mean state로
대체하지 않습니다. native plume clock은 `2 Q_integral/q`이므로 실제 source
경과시간 t의 filling front는 native clock **2t**에 있습니다. 적분질량 Q=q t까지
정상 공간 plume을 채우고, 해당 수용점이 front 뒤에 들어오면 그 위치의 정상
농도를 유지합니다. 수평/수직 shape를 단면 적분 1로 정규화하고 native의 단위길이
방출물 질량을 곱합니다. 이는 source-to-front 이동을 나타내는 보존적 filling-front
근사이며, front 종방향 확산을 별도로 풀지 않습니다. 종료 시 source가 계속
활성임을 명시하므로 낮은 마지막 수용점 농도를 방출 완료로 해석하지 않습니다.

### 변동 유량과 0 구간

각 양의 일정 구간은 자신의 시작시각을 offset으로 갖습니다. finite 구간은
각 종료 뒤 native puff로 이동하고, 마지막 continuous 구간만 계속 공급됩니다.
농도·증기체적과 방출물 질량을 합산합니다. 합친 체적분율>1이면 clip하지 않고
모델 범위를 벗어난 것으로 실패합니다. 이 검사는 상호작용 근사의 물리적 정확성을
검증하지는 않습니다. 심하게 겹치는 구름·비선형 혼합·운동량의 구간 간 전달이
중요한 경우 결합된 가변유량 solver가 별도로 필요합니다.

## 출력·질량수지

`ReleaseHistoryOutput`은 기존 histories와 sample_times를 유지해 history-dose 및
기존 DAG에 연결합니다. 추가 내용은 다음과 같습니다.

- 원본 source/request digest, 엔진 hash·버전·dependency versions
- source 누적질량과 공간 정규화 구름의 방출물 질량 시간배열
- segment별 유량·기간·총질량·used source area·전이 시각/위치
- native 시각·mode·center x·accounted mass 배열
- native puff 총질량, post-source steady flux, 전이 질량, 전이 cut flux 잔차
- source_active_at_window_end 및 명시적 reconstruction/coupling 명칭

native 시각은 segment의 **원래 local clock**을 보존하며 start_s는 별도 offset입니다.
`native_clock_kind`는 continuous plume의 2Q/q clock과 finite source/puff clock을
구분합니다. source region 내의 유량 증가를 full-rate steady flux로 잘못 검사하지
않습니다. 정확히 같은 native clock 행은 첫 행을 유지하고 제거 개수를 기록합니다.
실제로 역전한 clock은 실패입니다. 보간 없는 전이 cut 행은 유지됩니다.

검사는 PRISM ∑qΔt=선언질량, 각 finite puff의 `4 rho Bx By h mass_fraction=qT`,
source region 밖 plume의 `2 rho U By h mass_fraction=q`, 전이 재구성 질량 일치,
합성 후 누적질량 일치를 구분합니다. native source 보존 gate는 상대 1e-5이며
새 합성 사례에서는 훨씬 작은 잔차입니다. 재구성 단계에서 질량 정규화를 강제한다는
사실 자체를 물리적 검증으로 간주하지 않습니다. 전체 유입 공기 질량이나 실험자료
검증을 수행한 결과도 아닙니다.

## 실행과 검증

```text
python examples/ccps_release_history.py --output artifacts/ccps-finite.json
python examples/ccps_release_history.py --mode continuous_through_window --output artifacts/ccps-continuous.json
python examples/ccps_release_history.py --mode variable --output artifacts/ccps-variable.json
python -m pytest -q tests/test_ccps_release_history.py
```

기존 `POST /api/ccps/calculate`와 workflow에 새 ID를 사용할 수 있습니다.
`release.histories`, `release.sample_times_s`를 history-dose로 참조하고 기존
probit·PHA LOC risk 경로로 이어갑니다. 원래 PHA frequency credit 소유권과
baseline/code hash 검사 및 SQLite 저장은 변경하지 않았습니다.

시험은 PRISM left-hold endpoint/액체/질량 gate, 일정 source 분할 불변성, 0 유량
간격, finite 전이·질량·감쇠, continuous 정상 극한, 변동 구간 합성, T±δ 연속성,
240→480 native step·1→0.5 s 출력 세분화, 부족한 x grid 실패, HTTP/DAG·dose를
검증합니다. 모두 새 합성 값이며 원문 예제·실측 data는 포함하지 않습니다.
실제 SLABx 실행 시험이며, 임의유량 결합모델의 과학적 검증이나 현장검증·기관의
적합성 인증을 주장하지 않습니다.
