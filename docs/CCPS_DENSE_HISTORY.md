# 고밀도 확산 농도·시간이력 API

후속 확장: 연속·유한시간 source와 PRISM left-held 매핑은 별도
`dispersion/slabx-release-history` 계약으로 추가했습니다.
[전이·질량수지·근사 경계](CCPS_RELEASE_HISTORY.md)를 참고하세요.
아래 `slabx-instantaneous` 계약은 그대로 유지합니다.

## 선택한 모델과 범위

실제 선택형 **SLABx 1.0.8**을 별도 Python 프로세스에서 실행합니다.
`dispersion/slabx-instantaneous`는 순간 지상 순수증기 방출을 대상으로 구름의
시간별 위치·크기·밀도·혼합 상태를 적분하고, 고정 수용점의 kg/m³·체적분율
시간응답을 재구성합니다. Richardson 선별 결과나 정상 Gaussian 농도를 시간축에
복사하는 경로가 아닙니다. 기본 설치의 기존 FTA/LOPA/SIL/단순 결과분석은
SLABx 없이 계속 사용할 수 있습니다.

공개 근거와 확인한 코드 경계:

- [EPA SLAB 소개와 원 매뉴얼 링크](https://www.epa.gov/scram/air-quality-dispersion-modeling-alternative-models#slab):
  momentum·mass/species·energy·상태방정식을 이용하는 dense 모델 계열.
- Ermak (1990), UCRL-MA-105607, §2.3.2 순간 puff, 식 15–28의 상태·농도 프로파일.
  매뉴얼은 위 공식 EPA 링크에서 별도로 취득합니다.
- [SLABx 원저장소](https://github.com/lyullee/slabx): 로컬 설치 버전 1.0.8의
  `core.source.InstantaneousRelease`, `core.plume.run_dispersion`, `core.trajectory`,
  `post.concentration` 인터페이스를 검토했습니다. 외부 엔진은 재구현물이며,
  SLAB 원본이나 기관의 적합성 인증과 동일시하지 않습니다.
- 로컬 PRISM의 `slabx_provider_boundary.py`, `inventory_source.py`와 기존 PHA
  `PrismClient`도 검토했습니다. PRISM 경계는 유량·기액분할·이력을 소유합니다.
- 인접 API-581의 SLABx 어댑터는 pool/jet 공간별 최대농도 경로입니다.
  해당 최대농도 배열을 고정 수용점 시간응답으로 재해석하지 않았습니다.

## PRISM·SLAB의 연동 결정

| 단계 | 소유자 | 이번 연결 |
|---|---|---|
| 방출원·재고·기액분할·시간이력 | PRISM 또는 명시적 사용자 모델 | 새 `DenseInventory`로 **이미 자격을 확인한 순간 증기 재고**만 수용 |
| LOC 빈도·방호계층 credit | PHA FTA/LOPA/SIL | 기존 `frequency_from_study` 및 `run_consequence_workflow` 유지 |
| dense 구름 적분 | 별도 설치 SLABx 1.0.8 | 핀된 소스 해시, 프로세스 격리, 버전 확인 |
| 고정 수용점 시간응답 | 새 자체 작성 postprocessor | 순간 puff 유사분포의 정규화·상태 보간 |
| 노출 적분·합성 harm·risk | 기존 결과분석 API | history-dose → probit → conditional risk DAG 연결 |

PRISM 연속 방출·LH2 액적 packet을 통째로 한 puff에 넣는 자동 변환은 없습니다.
`origin="prism"`은 원본 provenance 레이블이며 PRISM을 새로 실행했다는 표지가
아닙니다. 원본 digest, code digest, 자격확인 근거, 설비·시나리오·운전 ID를
기록해야 합니다. 현재 실제 엔진 시험은 **SLABx baseline 순간 증기 경로**입니다.
기존 PRISM 회귀시험은 별도로 유지하며, 새로운 PRISM-LH2 시간응답 경로를
실행·검증했다고 주장하지 않습니다. SLABx-LH2 보정·연속 공급·2상/액적·공간 장애물은
각각 전용 입력/검증이 필요한 다음 경계입니다.

## 입력 계약과 실행

```text
python -m pip install -e ".[test,dense]"
python examples/ccps_dense_history.py --output artifacts/ccps-dense.json
```

```python
from ccps_consequence import calculate
from ccps_consequence.dense import capabilities

engine = capabilities()  # 별도 프로세스: status/version/code hash/dependency versions
# reviewed_inputs/context는 아래의 명시적 계약에 맞춰 준비합니다.
# reviewed_inputs["expected_engine_code_digest"] = engine["engine_code_digest"]
# receipt = calculate("dispersion/slabx-instantaneous", reviewed_inputs, context=context)
```

예제의 synthetic property·기상·재고 입력은 새로 작성했으며 실제 물질 DB나
CCPS/SLAB 매뉴얼 예제의 수치가 아닙니다. 예제는 probe 결과를 명시적으로 핀한 뒤
실행합니다. 운영에서는 검토한 engine hash를 보관하고 재사용해야 하며 매번
새 fingerprint를 무조건 신뢰하는 정책은 이 API가 제공하지 않습니다.

| 입력 | 단위·제약 |
|---|---|
| source | `ccps.instantaneous-source.v1`: asset/scenario/operating_case, origin, source/code digest, evidence IDs, `instantaneous_pure_vapour`, mass_kg>0, area_m2>0, temperature_k, qualification_basis |
| substance | 이름, molecular_weight_kg_mol (**kg/mol**), vapor/liquid heat capacity J/kg/K, latent heat J/kg, boiling K, liquid density kg/m³, property_basis |
| atmosphere | wind m/s, reference height m, K, humidity fraction [0,1], roughness m, stability A..F, 101325 Pa 고정 |
| receptors | 고유 ID, downwind>=0 m, signed crosswind m, height>=0 m; 최대 32개 |
| sample_times_s | 0에서 시작하는 증가 배열, 마지막 값은 simulation_end_s; 2..2001개 |
| simulation_end_s | 0< t <=86400 s, 적분 종료시간을 명시 |
| native_puff_steps | 80..2000, default 240; native 적분 출력 격자 |
| expected_engine_code_digest | 사용자가 승인한 설치 엔진 Python 소스 SHA256 |
| tail_threshold_kg_m3 | >0, 끝단 농도 진단 기준이며 독성 종말점으로 해석하지 않음 |
| timeout_s | 0< t <=300 s, default 60 |
| applicability | `instantaneous_ground_vapour_flat_terrain_no_meander` 고정 |

요청별 수용점×시간 표본은 최대 32000입니다. source/context identity·근거참조,
순수증기 경계, 풍속·높이·roughness, 유한값·타입을 검증합니다.
초기 밀도가 대기보다 가볍거나, 초기 구름이 mixing height를 넘거나,
native 온도가 입력과 달라지거나, 방출물의 응축이 나타나는 경우 실패합니다.
기관이 검증한 물성 범위를 자동 판단하지 않습니다. 연료·기상·상수물성의 적용성은
호출자의 근거에 남겨야 합니다. 외부 엔진 미설치/버전불일치/해시불일치/timeout도
명시적 실패이며 Gaussian·다른 checkout·다른 엔진으로 대체하지 않습니다.

## 시간응답 계산의 의미

SLABx의 순간 방출 경로는 전 구간 puff입니다. source area는 square footprint이고
초기 재고는 t=0에 모두 존재합니다. dense 동역학은 외부 solver가 계산합니다.
자체 postprocessor는 시각 t의 중심 X(t), zc(t), bx/by, beta_x/y, sigma_z와
방출물 질량·증기체적을 native 시간격자에서 사용자 표본시간으로 **선형 보간**합니다.
시간 격자 밖으로 외삽하지 않으며 최종시간의 부동소수 오차만 1e-12 상대 허용합니다.

수평 shape는 erf 차이고 적분은 각 방향에서 4b, 지면 반사된 수직 Gaussian의
적분은 sqrt(2 pi) sigma입니다. 세 shape 곱을
`16 bx by sqrt(2 pi) sigma_z`로 나누면 적분값이 1인 공간 kernel이 됩니다.
그 kernel에 native 방출물 질량을 곱해 kg/m³, native 방출증기 체적을 곱해
체적분율을 구합니다. 위치는 receptor_x-X(t)로 평가하므로 구름을 따라가는
최대농도와 고정 수용점 응답을 구분합니다. meander·센서 시간평균은 적용하지 않은
**instantaneous ensemble mean**입니다.

거의 순수한 초기 source 내부에서 유사분포가 체적분율>1을 만들면 clip하지 않고
오류를 반환합니다. 너무 가까운 수용점이나 해당 프로파일의 유효성 문제를 숨기지
않습니다. 초기에 재고를 순간적으로 놓는 이상화 및 상수물성 thermodynamics의
적용성을 별도로 검토해야 합니다.

## 출력·질량수지·노출 적분

영수증의 원래 input/output/code hashes와 evidence·section·method references를
보존합니다. 결과에는 SLABx 소스 해시·버전, NumPy/SciPy 버전, request digest,
실제 native 시각·중심위치·방출물 질량, 사용자가 요청한 시각·수용점별
kg/m³·체적분율·표본 최대값·최대 시각·표본 trapezoid 적분을 포함합니다.
원시 상태의 방출물 질량은 `4 rho Bx By h mass_fraction`으로 검사하고 최대 상대
오차>1e-5이면 결과를 거부합니다. 이는 외부 solver의 방출물 질량수지 검사이며
실측 물리검증이나 도메인 전체 유입공기 질량수지 검증을 뜻하지 않습니다.

끝단 진단:

- `end_above_threshold`: 마지막 농도가 입력 기준 이상.
- `end_below_threshold_peak_at_end`: 마지막 농도는 기준 아래지만 최대값이 끝단.
- `end_below_threshold`: 마지막 농도가 기준 아래이고 최대값은 앞 구간.

마지막 상태가 낮더라도 관측 창 밖의 영구 무노출·정확한 도착/종료 시각을 증명하지
않습니다. 최대값·적분은 표본격자에 따른 값입니다. 시간창·표본간격·native step을
세분화하여 확인해야 합니다. 누락된 꼬리를 0으로 붙이지 않습니다.

`dispersion/history-dose`는 `sample_times_s`, `histories`, `receptor_id`,
`exponent`, `reference_value_kg_m3`, `integration="sampled_trapezoid"`를 받습니다.
`normalized_dose_s`, `observation_end_s`, `tail_status`를 반환합니다.
각 시각의 `(C/reference)^exponent`에 trapezoid를 적용하므로 평균농도를 먼저
제곱하지 않습니다. 이 값은 지정한 시간창의 sampled quadrature입니다.
독성계수·인체 harm 모델은 새로 넣지 않았습니다.
Python helper `history_dose_input`도 기존 `effects/dose`에 같은 적분을 연결합니다.

## HTTP·DAG·저장

`GET /api/ccps/dense/capabilities`로 설치 정보를 얻고 기존
`POST /api/ccps/calculate`에 새 ID를 전달합니다. 기존 workflow에서도:

```json
{
  "id": "dose",
  "calculation_id": "dispersion/history-dose",
  "inputs": {
    "sample_times_s": {"$ref": "dense.sample_times_s"},
    "histories": {"$ref": "dense.histories"},
    "receptor_id": "R60",
    "exponent": 1.0,
    "reference_value_kg_m3": 0.01,
    "integration": "sampled_trapezoid"
  }
}
```

이후 dose→probit→risk 참조를 이어갈 수 있습니다. 통합 시험은 실제 dense worker와
기존 PHA LOC 빈도를 결합하는 4단계 DAG를 실행합니다. PHA 계산은 source의 물리적
도출을 검증하지 않으며 합성 연결 시험으로만 기록합니다. 기존 baseline workflow
저장 경로를 쓰면 영수증·의존성·성공/실패가 SQLite에 남습니다.

## 검증과 배포 경계

```text
python -m pytest -q tests/test_ccps_dense.py
python -m pytest -q --junitxml=verification/ccps-pha-tests.xml
```

독립 shape 적분·질량 정규화, native 소규모 평균시간 농도와 자체 kernel의 중심선
극한 일치, 실제 수용점 지연·측풍감쇠·시간감쇠, native 240→480 step 및 표본
1→0.5 s 세분화, mass ledger, 잘못된 fingerprint, 응답 shape, timeout, missing
optional package, HTTP·DAG·PHA risk 연결을 검사합니다. 외부 엔진이 없으면 실제
native 시험만 skip되며 수학·계약 시험은 실행됩니다.

영수증의 `validation_level="native_engine_executed"`는 실행 사실이지 외부 인증이나
현장검증 수준이 아닙니다. source·CCPS 원문·SLAB 매뉴얼·Fortran·SLABx 소스·
실험관측 자료는 저장소와 wheel에 포함하지 않습니다. 선택형 `slabx==1.0.8`만
dependency로 선언합니다. SLABx는 설치 메타데이터의 MIT 조건을 별도로 따르며
외부 소프트웨어의 원출처·비clean-room 주의사항을 자체 구현의 권리로 대체하지 않습니다.
