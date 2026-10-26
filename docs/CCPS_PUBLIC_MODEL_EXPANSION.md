# 공개 근거 기반 확장 — 2026-10-26

## 우선순위와 선정 이유

| 우선순위 | 영역 | 이번 구현 | 이후 경계 |
|---|---|---|---|
| 1 | 화재 | 공개 식이 명확한 fireball 크기·시간, 구형 view factor, solid-flame 열유속, 풀 질량·에너지 수지 | 상세 jet/pool 형상·연소율 예측·BLEVE 파열·fireball 상승은 외부 모델 |
| 2 | 폭발 | EPA의 1 psi 고정 종말점 거리 | 임의 과압·충격량, BST/TNO 곡선, 구속·혼잡·파열 모델은 외부 모델 |
| 3 | 고밀도 확산 | friction Richardson 수와 명시적 적용성 선별 | 농도·시간이력·중력확산·entrainment·열수지는 검증된 외부 solver 필요 |

화재는 공개 식의 입력·출력·기하학적 범위가 명확하고 기존 dose/threshold와 바로
연결할 수 있어 먼저 구현했습니다. 폭발은 특정 종말점의 식만 수용했습니다.
고밀도 농도 예측은 여러 연성 방정식·경험 closure와 검증 자료가 필요하므로
단순한 Gaussian 대체나 근거 없는 box-model을 추가하지 않았습니다.
선별기는 모델 선택 근거를 남기는 진단이며 자동 라우터가 아닙니다.

## 공개 출처와 식

NOAA NOS OR&R 43 (2013), ALOHA 5.4.4 Technical Documentation:
[공식 기술문서](https://response.restoration.noaa.gov/sites/default/files/ALOHA_Tech_Doc.pdf),
[공식 권리·서지 메타데이터](https://repository.library.noaa.gov/view/noaa/2669).
페이지는 PDF 1-based / 인쇄 페이지를 함께 기록합니다.

- §4.4.1, PDF 54–55 / 인쇄 46–47: g'=g(rho_cloud-rho_air)/rho_air,
  Ri=H g'/u_star²; 임계 1의 diagnostic.
- §6.1, PDF 73 / 인쇄 65: q=E F tau. E·F·tau는 입력이며 내부 데이터베이스 없음.
- §6.3.2, PDF 76 / 인쇄 68: D=5.8 M^(1/3), M은 사용자가 지정한 참여 연료 kg.
- §6.3.2, PDF 77 / 인쇄 69: 지면에 접하는 구와 지면 수직 수용점의
  F=r² x/(x²+r²)^(3/2), x>r.
- §6.3.4, PDF 77 / 인쇄 69: t=0.852 M^0.26, t는 s.

풀 수지는 공개 열방출 모델 계열에 연결한 자체 conservation wrapper입니다.
NOAA가 이 wrapper의 재고 절단 알고리즘을 규정한다고 주장하지 않습니다.
연소율=면적×입력 burning flux, 연소량=min(재고, 연소율×시간),
활성 열방출률=연소율×연소열×효율, 에너지=연소량×연소열×효율입니다.
영 연소량에서는 활성 열방출률도 0을 반환합니다. 활성 HRR는 연소 중의 값이며
요청 구간 전체의 평균이 아닙니다.

EPA-550-B-99-009 (1999), Appendix C.1, equation C-1, PDF 19 / 인쇄 C-1:
[공식 Appendix](https://www.epa.gov/sites/default/files/2017-05/documents/oca-apds.pdf).
W_TNT=0.1 M Hc/(4,680,000 J/kg), 거리=17 W_TNT^(1/3) m.
출력 종말점은 1 psi=6894.757293168 Pa로 고정됩니다. 이 API는 현재 규제 해석이나
현장 최악 시나리오의 충족 여부를 판단하지 않습니다.

## 추가 API 계약

기존 `calculate(id, inputs, context=...)`, schema bundle, receipt, workflow를 그대로
사용합니다. `Receipt.method_references`는 default가 빈 tuple인 추가 필드입니다.
신규 계산은 여기에 공개 근거 URL·PDF 페이지를 넣습니다. 기존 ID·입출력 필드는
유지하며, source hash 변경으로 이전 코드 영수증은 stale입니다.

| ID | 필수 입력·SI 단위 | 출력·SI 단위 | 거부 조건·제한 |
|---|---|---|---|
| dispersion/richardson-screen | cloud_density_kg_m3, air_density_kg_m3, characteristic_dimension_m, friction_velocity_m_s, gravity_m_s2, characteristic_dimension_basis, applicability | reduced_gravity_m_s2, friction_richardson_number, screening, concentration_prediction_available=false | 비양수 rho/H/u_star/g; dense 농도는 미산출 |
| fire/fireball | participating_mass_kg, mass_basis, correlation | diameter_m, duration_s | 0<M<=5,000,000 kg; 참여질량 자동 추정 없음 |
| fire/solid-flame | surface_emissive_power_w_m2, view_factor, transmissivity, emissive_power_basis, view_factor_basis, applicability | heat_flux_w_m2 | F,tau는 [0,1], E>=0; 형상 예측 없음 |
| fire/sphere-radiation | diameter_m, horizontal_distance_m, surface_emissive_power_w_m2, transmissivity, emissive_power_basis, geometry | view_factor, heat_flux_w_m2 | x>diameter/2, 지면접구·지면의 화염방향 수직 수용점만 |
| fire/pool-energy | area_m2, burning_flux_kg_m2_s, inventory_kg, duration_s, heat_of_combustion_j_kg, combustion_efficiency, burning_flux_basis, applicability | mass_rate_kg_s, burned_mass_kg, remaining_mass_kg, effective_duration_s, heat_release_rate_w, released_energy_j | 일정 면적·flux, 재공급 없음; 연소율 상관식 아님 |
| explosion/epa-1psi | flammable_mass_kg, heat_of_combustion_j_kg, mass_basis, applicability | equivalent_tnt_mass_kg, endpoint_distance_m, endpoint_pressure_pa, explosion_efficiency, tnt_specific_energy_j_kg | 10% yield·TNT 에너지·종말점 고정; 임의 endpoint 입력 거부 |

정확한 enum과 bounds는 생성 schema에 있습니다. 기존과 같이 NaN/Inf·bool·문자열
숫자·extra field를 거부하고 overflow는 성공 결과로 반환하지 않습니다.
경량화된 공개 상관식의 유효성은 연료·사고조건에 따라 검토해야 합니다.
fireball mass 상한은 NOAA 구현의 제한을 보존한 것이며 해당 구간 전체에 대한
실험 검증을 뜻하지 않습니다. 압축기체 fireball·분진·반응성 폭발 적용을 주장하지 않습니다.

Ri<1이고 rho_cloud>=rho_air이면 `passive_candidate`, Ri>=1이면
`dense_model_required`, rho_cloud<rho_air이면 `buoyant_review_required`입니다.
음의 Ri는 보존하지만 상승하는 플룸의 높이·농도를 예측하지 않습니다.
friction velocity는 지상 10 m 풍속과 다르며, 둘 사이의 자동 변환은 없습니다.
H의 source-specific 산정과 근거는 호출자가 제공합니다.

## 실행 예제와 연동

```python
from ccps_consequence import Context, calculate

r = calculate("fire/fireball", {
    "participating_mass_kg": 8.0,
    "mass_basis": "synthetic participating fuel",
    "correlation": "noaa_2013_roberts_diameter_dutch_duration",
}, context=Context(asset_id="T1", scenario_id="fireball", operating_case_id="normal"))
print(r.outputs)  # diameter_m=11.6, duration_s=0.852*8**0.26
print(r.method_references)
```

`examples/ccps_fire_explosion.workflow.json`은 8단계 합성 예제입니다.
fireball → sphere → dose와 pool energy → 점원복사를 연결하고,
같은 형상의 solid-flame 결과 일치, 독립적인 폭발 종말점·dense screening을 보여줍니다.
각 경로를 하나의 실제 사고의 동시 결과로 합산하지 않습니다.
연소율·emissive power·기상은 합성 입력입니다. dose에는 임의의 정규화 기준만
사용하며 인체 피해계수는 추가하지 않았습니다.

FTA/LOPA/SIL의 LOC 빈도 계약과 risk factor 소유권은 변경하지 않았습니다.
API-581·PRISM의 source/provider 경계도 유지합니다. 신규 식은 native 계산으로
실행되고, 외부 농도 solver가 필요한 경우 기존 provider를 명시적으로 주입합니다.
기존 HTTP calculate/workflow 경로에서 신규 ID를 즉시 사용할 수 있습니다.

## 추적성·검증·저작권

각 ID는 CCPS 주제 섹션→공개 식 위치→Python 입력·출력 schema→직접 시험→
실행 영수증으로 연결됩니다. CCPS 섹션은 주제 분류이고 식의 직접 근거는 공개
NOAA/EPA 문서입니다. 원문·그림·표·예제답·외부 엔진 소스는 저장하지 않았습니다.
시험은 새 합성 수치와 경계값, 차원, 질량/에너지 보존, 기하학적 항등식,
cube-root scaling, 재실행 및 스키마 일치를 사용합니다.
외부 독립평가·ALOHA 일치 인증·현장검증·CCPS 적합성은 주장하지 않습니다.
