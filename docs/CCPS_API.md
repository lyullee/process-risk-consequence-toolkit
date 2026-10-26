# CCPS 결과분석 Python API v0.1

2026-10-26 연구용 1D 결합 모델까지 포함해 총 23개 계산입니다.
[결합 모델](CCPS_COUPLED_LAYER.md)은 기존 SLABx 경로와 별도의 등온·고정 폭 연구 API입니다.
[방출 이력·plume-to-puff 계약](CCPS_RELEASE_HISTORY.md)에 source 매핑·질량수지와 근사 범위를 기록했습니다.
[SLABx 순간 증기 농도·시간응답](CCPS_DENSE_HISTORY.md)에 새 계약과 실제 엔진 검증을 기록했습니다.
먼저 추가된 6개 ID의 우선순위,
식·단위·실패조건·직접 출처는 [공개 모델 확장](CCPS_PUBLIC_MODEL_EXPANSION.md)에 있습니다.

## 구현 범위와 자료 경계

`ccps_consequence`는 독립적으로 import할 수 있는 Python namespace입니다.
기본 계산 패키지는 표준 라이브러리와 Pydantic만 사용하며, `pha_core`, API-581,
PRISM을 import하지 않습니다. 배포 단위는 기존 `pha-core` wheel에 함께 포함됩니다.
HTTP 호스트는 기존 FastAPI입니다. 프론트엔드는 변경하지 않았습니다.
고밀도 실제 계산은 선택형 SLABx를 새 프로세스에서 import합니다. host의
기본 import나 schema 조회에서는 외부 엔진을 import하지 않습니다.

CCPS/AIChE 자료를 분류 기준으로 삼되, 원문의 디지털 복제·전체 구현·적합성을
주장하지 않습니다. CCPS PDF는 외부 로컬 자료로만 검토했습니다. 원문, 추출문,
표, 그림, 상용 프로그램, 원문 예제의 입력·답은 저장하지 않습니다.
검토 메타데이터와 계획은 [IMPLEMENTATION_HISTORY.md](IMPLEMENTATION_HISTORY.md),
섹션→계산→시험 연결은 [CCPS_TRACEABILITY.md](CCPS_TRACEABILITY.md)에 있습니다.

공개 기술 맥락은 NOAA Technical Memorandum NOS OR&R 43 (2013),
[공식 자료 및 권리 메타데이터](https://repository.library.noaa.gov/view/noaa/2669),
[공식 기술문서](https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf)의
source strength, passive Gaussian dispersion, radiation 모델 계열을 검토했습니다.
이 패키지는 ALOHA 복제나 ALOHA 수치 일치 구현을 주장하지 않습니다.
식은 아래에 명시한 일반 물리·수학의 screening primitive로 자체 작성했습니다.
공개 참조문서 자체도 저장소에 복사하지 않습니다.

## 계산과 단위

모든 수치는 유한한 SI 값입니다. 압력은 절대압 Pa, 온도는 K, 시간은 s,
질량은 kg입니다. bool, 문자열 숫자, NaN/Inf, 음수 질량·시간, 알 수 없는 필드는
거부합니다. 모델은 frozen이며, dict를 포함한 결과의 저장·전달 후에는
`verify_receipt`로 재계산 검증할 수 있습니다. 해시는 전자서명이나 인증이 아닙니다.

| ID | 계산 | 주요 제한 |
|---|---|---|
| source/liquid | Cd A sqrt(2 rho (Pu-Pd)) | 비압축·비플래싱 단공; 역차압 거부 |
| source/gas | 이상기체 등엔트로피 단공, 임계 압력비로 choked/subsonic 구분 | 고정 저장상태, real gas·배관·2상 제외 |
| source/inventory | min(inventory, rate × duration) | 일정 방출률, 재공급 없음 |
| source/flash | clip(cp (T-Tb)/Lv, 0, 1), 기액 질량분할 | 일정 물성·현열 근사; aerosol/EOS 제외 |
| source/evaporation | 입력 flux × area, inventory 제한 | flux 예측기 아님; 풀 에너지수지 제외 |
| dispersion/plume | 반사 지면을 갖는 정상 Gaussian 점원 | 수동·정상·개방지형; sigma는 사용자 입력 |
| dispersion/puff | 이류하는 순간 Gaussian puff와 지면 반사 | sigma와 경과시간 관계는 사용자 책임 |
| effects/radiation | HRR × fraction × transmissivity / (4 pi r²) | 원거리 등방 점원; 화염형상 계산 아님 |
| effects/dose | sum((value/reference_value)^exponent × duration_s) | 무차원화된 강도와 시간의 적분, 결과 s |
| effects/probit | Phi(intercept + slope ln(dose/reference_time) - offset) | 영 dose는 0; 계수·기준·단위 명시 필수 |
| effects/tnt-scaling | mass × heat × efficiency / TNT energy, r / W^(1/3) | 압력/충격량 곡선 없음; 영 에너지 scaled distance는 null |
| effects/threshold | value >= threshold, value/threshold | 단일 수용점 비교; 치사확률·영향거리 아님 |
| risk/conditional | LOC frequency × branch probability × harm × explicit factors | 한 시나리오·수용점의 빈도기여도; 시설 전체값 아님 |

정상 plume은 Q/(2 pi u sigma_y sigma_z)에 수평 Gaussian과 두 개의 수직
Gaussian(z-H, z+H)을 곱합니다. Puff는 M/((2 pi)^1.5 sigma_x sigma_y sigma_z)에
x-u t, y, z±H 항을 곱합니다. Plume의 downwind distance는 sigma 적용 위치를
명시하는 메타입력이며, sigma 상관식을 내부에서 추정하지 않습니다.
연속 plume의 도달시간·방출 지속시간은 호출자가 검토합니다. 예제는
60 m / 3 m/s 도달시간 이후의 10 s 노출을 가정한 합성 정상근사입니다.

고밀도·극저온 확산, 2상 방출, 비정상 탱크 열역학, 상세 풀 증발,
상세 화염형상·BLEVE 파열·fireball 동역학·flash fire 영역, VCE blast curve, confined/physical
explosion, 회피행동은 외부 모델 경계입니다. `calculate("dispersion/dense-gas", ...)`
같은 미등록 ID는 명시적 예외를 내며 다른 식으로 대체하지 않습니다.
등록된 부분 계산도 해당 장 전체의 구현을 의미하지 않습니다.
순간 지상 순수증기 dense puff만 선택형 실제 SLABx 경로로 계산하며,
그 밖의 source/연속 공급/액적/LH2 보정은 전용 외부 경계로 유지합니다.
fireball의 크기·시간·구형 view factor, 공급된 형상의 solid-flame 열유속,
풀 연소 에너지 수지, 고정 1 psi 폭발 거리와 dense Richardson 진단은
공개 근거 확장 API로 부분 구현했습니다. 기존 선별 계산의 제약도 그대로 유지됩니다.

## Python 실행

계산별 입력·출력 필드의 정확한 required/default/enum/type은
`contracts/ccps.contracts.v1.schema.json`의 `calculations[ID].input/output`에
고정되어 있으며, 다음 표는 입력과 실패조건을 요약합니다. 모든 경로는
context의 asset/scenario/operating_case와 영수증의 evidence_ids를 보존하고,
`CCPS_TRACEABILITY.md`의 직접 시험에 연결됩니다.

| ID | 입력 필드·단위 | 출력 필드·단위 | 주요 실패조건 |
|---|---|---|---|
| source/liquid | area_m2, density_kg_m3, upstream/downstream_pressure_pa_abs, discharge_coefficient[0..1], phase | mass_rate_kg_s, regime | 역차압, 비양수 면적·밀도·압력, 잘못된 phase |
| source/gas | area_m2, upstream/downstream_pressure_pa_abs, temperature_k, specific_gas_constant_j_kg_k, heat_capacity_ratio(1..2], discharge_coefficient, phase | mass_rate_kg_s, regime | 역차압, k<=1, 잘못된 phase |
| source/inventory | mass_rate_kg_s, duration_s, inventory_kg | released_mass_kg, remaining_mass_kg, effective_duration_s | 음수·비유한 값 |
| source/flash | mass_kg, liquid_heat_capacity_j_kg_k, initial/boiling_temperature_k, latent_heat_j_kg, assumption | vapour_fraction[0..1], vapour_mass_kg, liquid_mass_kg | 비양수 물성·K, 지정 assumption 불일치 |
| source/evaporation | area_m2, mass_flux_kg_m2_s, duration_s, inventory_kg, flux_basis | released_mass_kg, remaining_mass_kg, effective_duration_s | flux 근거 없음, 음수 flux |
| dispersion/plume | mass_rate_kg_s, wind_speed_m_s, downwind/crosswind_distance_m, receptor/release_height_m, sigma_y/z_m, sigma_basis, applicability | concentration_kg_m3 | wind/sigma/downwind<=0, dense gas 등 applicability 불일치 |
| dispersion/puff | mass_kg, downwind/crosswind_distance_m, receptor/release_height_m, wind_speed_m_s, elapsed_s, sigma_x/y/z_m, sigma_basis, applicability | concentration_kg_m3 | wind/sigma/time<=0, 잘못된 applicability |
| effects/radiation | heat_release_rate_w, radiative_fraction, transmissivity, distance_m, applicability | heat_flux_w_m2 | 거리<=0, 비율 범위 이탈, 원거리 점원 가정 불일치 |
| effects/dose | values[], durations_s[], exponent, reference_value, reference_unit(kg/m3,W/m2,Pa) | normalized_dose_s | 빈 배열·길이 불일치, 비양수 reference/exponent/duration |
| effects/probit | normalized_dose_s, reference_time_s, intercept, slope, normal_offset, coefficient_basis | probability[0..1] | 계수 근거 없음, slope/reference_time<=0 |
| effects/tnt-scaling | flammable_mass_kg, heat_of_combustion_j_kg, explosion_efficiency, tnt_specific_energy_j_kg, distance_m, efficiency_basis | equivalent_tnt_mass_kg, scaled_distance_m_kg_third 또는 null | 비양수 에너지·거리, 효율 범위 이탈·근거 없음 |
| effects/threshold | value, threshold, unit(kg/m3,W/m2,Pa), criterion_basis | exceeded(bool), ratio[1] | threshold<=0, 기준 근거 없음 |
| risk/conditional | frequency(LOC year^-1), receptor_id, branches[], partition_basis, mutually_exclusive_exhaustive | annual_harm_frequency_per_year, branches[] | 분기합!=1, 중복 factor, 빈도/context/근거 불일치 |

모든 계산의 알려지지 않은 필드·미등록 ID·수치 overflow는 성공 결과로
승격되지 않습니다. Numeric bounds의 세부사항은 generated schema를 기준으로 합니다.

프로젝트 폴더에서 `python -m pip install -e ".[test]"` 후:

```python
from ccps_consequence import Context, calculate, verify_receipt

context = Context(asset_id="T1", scenario_id="leak", operating_case_id="normal")
receipt = calculate("source/inventory", {
    "mass_rate_kg_s": 2.0, "duration_s": 8.0, "inventory_kg": 10.0
}, context=context)
assert receipt.outputs["released_mass_kg"] == 10.0
verify_receipt(receipt)
```

`calculate`는 각 모듈의 `*Input` 객체도 받습니다. 직접 물리 함수는 typed
입출력을 반환하며, 감사 추적이 필요하면 반드시 `calculate`를 사용합니다.
JSON round-trip은 `Model.model_validate_json(...)`을 사용합니다. 엄격한 Python
모델의 tuple 필드에 Python list를 직접 전달하면 거부됩니다.

`calculation_catalog()`는 계산 ID·함수·부분 범위·공개 참고·시험 위치를 반환합니다.
`contract_schemas()`는 계산별 input/output, 영수증, DAG, 연동 계약의 독립
JSON Schema를 담은 인덱스를 반환합니다. `contracts/ccps.contracts.v1.schema.json`은
스키마 인덱스이며 그 자체를 단일 payload 검증용 JSON Schema로 사용하지 않습니다.
별도의 `ccps.receipt.v1.schema.json` 등은 Draft 2020-12 검증용 문서입니다.
확률합·질량수지·DAG·해시·근거참조 등 관계 검사는 Python 검증에서 수행합니다.

영수증에는 정규화 입력, 입력/출력 SHA256, 전체 CCPS 소스 코드 해시,
context/근거 ID, 섹션·제약, 소프트웨어 검증 수준을 포함합니다.
동일 소스·입력은 동일 영수증을 생성합니다. 원본 evidence 파일은 관리하지 않으며
근거 metadata/hash만 수용합니다. 운영 입력도 기본 결과 상태는 engineering review
required이고, 시험 통과가 현장검증·인증 상태를 부여하지 않습니다.

## DAG 워크플로

```python
from pathlib import Path
from ccps_consequence.workflow import Workflow, run_workflow

workflow = Workflow.model_validate_json(
    Path("examples/ccps_screening.workflow.json").read_text(encoding="utf-8")
)
result = run_workflow(workflow)
```

`{"$ref": "gas.mass_rate_kg_s"}`는 명시한 단계의 output 필드 참조입니다.
중첩 dict/list 내부에서도 사용할 수 있고, 전방참조는 DAG 순서로 실행합니다.
중복 단계, 없는 필드, 순환, 알려진 필드 사이 단위 불일치, 하류 타입 불일치를
거부합니다. 단위를 자동 변환하지 않습니다. 값·배열 안의 참조는 목적 단위가
명시된 경우 검사합니다. 이 검사는 모든 물리적 의미·모델 적용성 검토를 대체하지
않습니다. 예를 들어 서로 같은 SI 단위를 갖는 다른 물리량의 의미는 호출자가
검토해야 합니다. `WorkflowError.step_id`로 실패 단계를 식별하며, 실패한 DAG는
성공 워크플로 결과를 반환하지 않습니다. 각 성공 단계에는 부모 영수증 해시가 있습니다.

## FTA·LOPA·SIL 연동

PHA 소유 어댑터 `pha_core.ccps.frequency_from_study(snapshot, scenario_id, context=...)`는
현재 snapshot을 재검증하고 `analyze`를 호출하여 FTA, 저빈도 SIF, 기존/제안 LOPA를
재계산합니다. 전달한 analysis가 있으면 baseline/code hash와 재현한 계산을 비교합니다.
`loss_of_containment` 이후의 빈도만 수용하고 demand 빈도나 이미 consequence로
조건부화된 빈도는 거부합니다. `pha:<snapshot digest>` 근거 항목과 동일 sha256,
설비·시나리오·운전상태 일치를 요구합니다. 합성 snapshot은 합성 evidence/context를
유지합니다. upstream barrier와 transition ID를 `included_factor_ids`로 보존합니다.

`risk/conditional`은 upstream ID와 branch 확률·harm·occupancy 등 하류 ID의
중복을 거부합니다. 분기 확률은 1로 합쳐져야 하며, 누락된 잔여 분기는 harm=0 등으로
명시해야 합니다. 분기의 상호배타·완전성, 계수들의 조건부 의미는 사용자가 근거로
명시합니다. ID를 바꿔 같은 의미의 확률을 재사용하는 것은 자동 판별하지 못합니다.
출력은 annual harm **frequency**이며 연간 확률로 자동 변환하지 않습니다.

`run_consequence_workflow(snapshot, scenario_id, workflow)`는 모든 risk 단계의
frequency를 새로 계산한 PHA 계약과 일치시킨 후 DAG를 실행합니다. PHA code digest,
baseline digest, LOC 계약, CCPS DAG/영수증을 하나의 결과로 묶습니다.
`python examples/ccps_python_workflow.py`로 6단계 합성 통합 경로를 실행합니다.
PHA 과압 시나리오에 별도 합성 방출조건을 붙인 연결 예제이므로 현장 방출조건의
물리적 도출을 입증하는 사례가 아닙니다.

## API-581·PRISM 경계

| 경계 | 소유자 / 수용 내용 | 거부·제약 |
|---|---|---|
| ExternalSource | 외부 엔진 / 설비·시나리오·운전, engine/code/source hash, 일정 rate·duration·mass·phase | 질량수지 불일치, 근거 없음 |
| api581_release_source | API-581 Python receipt / release/gas 또는 release/liquid의 kg/s만 매핑 | COF 면적·POF를 방출률로 해석하지 않음; caller가 fingerprint·duration·근거 지정 |
| Frequency | PHA 또는 명시적 외부 제공자 / LOC year^-1 | probability와 frequency를 혼동하지 않음; API-581 빈도의 자동 선택 없음 |
| ProviderRequest | 호출자 / engine·model·기대 code hash·수용점·거리·quantity·settings | 자동 engine 검색·선택 없음 |
| ProviderResult | 외부 제공자 / request hash·engine/model/receptor/quantity·값·근거·제약 | request/code binding 불일치, 확률>1, 미해결 근거 |

`evaluate_provider(request, provider)`는 명시적으로 주입한 Python Protocol 구현만
호출합니다. provider 미설정은 실패입니다. 테스트의 SyntheticProvider는 계약
시험용이며 PRISM 실행이 아닙니다. 실제 PRISM·API-581의 licensed 모델 실행·환경·
transport authenticity는 provider 소유입니다. `settings`는 의도적으로 엔진별
opaque mapping이고, 실제 provider가 해당 모델의 입력 스키마로 검증해야 합니다.
현재 kernel이 임의 settings로 외부 엔진을 직접 실행하지는 않습니다.
기존 `pha_core.prism.PrismClient` 프로세스 연동 경로는 유지됩니다.

API-581 wire adapter는 신뢰된 외부 결과의 구조·핀된 해시·asset을 검사하는 매퍼이며,
외부 결과를 재계산하거나 인증하지 않습니다. PRISM 결과도 `provider_reported_unverified`
상태입니다. 외부 결과의 검토를 CCPS 자체 계산의 검증으로 격상하지 않습니다.

## HTTP·저장·재현

기존 API 호스트에서 다음 경로를 추가했습니다.

- `GET /api/ccps/catalog`, `GET /api/ccps/schemas`
- `POST /api/ccps/calculate`: calculation_id, context, inputs
- `POST /api/ccps/workflow`: Workflow JSON, 독립 계산용
- `POST /api/baselines/{sha}/ccps/frequency?scenario_id=...`: Context JSON
- `POST /api/baselines/{sha}/ccps/workflow?scenario_id=...`: PHA 결합 Workflow JSON,
  SQLite run에 성공/실패 및 결과 저장

PHA 결합 실행의 각 계산 영수증은 입력·출력·부모 lineage를 포함합니다.
전체 Workflow 입력은 receipt의 정규화된 단계 입력에서 추적하고 원래 Workflow의
해시도 보존합니다. 원래 `$ref` 표현까지 재현하려면 호출자가 Workflow JSON을 함께
보관해야 합니다. PHA 저장 코드 해시는 CCPS namespace도 포함하므로 두 패키지 중
어느 소스든 바뀌면 기존 run을 stale로 판단합니다. 실행 중 소스가 바뀌면 재시작을
요구합니다. 무제한 대형 DAG용 job scheduler는 범위 밖이며 현재 호스트는 동기 실행입니다.

## 검증 재생성

```text
python scripts/build_ccps_contracts.py
python -m pytest -q --junitxml=verification/ccps-pha-tests.xml
python examples/ccps_python_workflow.py
```

시험은 새 합성 수치, 독립 해석해, 질량수지, 임계점 연속성, 역제곱 법칙,
Gaussian 중심선, 영 dose, 분기확률합, 중복 credit, DAG 오류, HTTP/저장·재현을
확인합니다. 외부 독립평가·CCPS 수치 전수비교·현장검증은 수행하지 않습니다.
실제 외부 엔진 실행 여부는 검증 보고서에 별도로 기록합니다.
