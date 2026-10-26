# 시간변동 유량의 결합 고밀도 층 모델

## 구현 결정과 지원 범위

`dispersion/coupled-layer-1d`는 독립 구간의 계산 결과를 합산하지 않습니다.
하나의 Eulerian 격자에서 혼합물 질량·방출물 질량·운동량을 보존형으로 적분하고,
PRISM left-held 유량을 그 격자에 주입합니다. 조성이 달라지면 밀도와 중력압력이
바뀌며, 이후 유량은 이미 존재하는 구름의 상태 위에 작용합니다.
유한/연속 source의 구분은 source 공급 상태이며, 별도의 plume-to-puff 전환이나
구름 분할을 사용하지 않습니다. 기존 SLABx 경로와 함께 선택할 수 있는 새 API입니다.

이번 결과는 **연구용 1차원·등온·평탄지형·고정 폭·수직 완전혼합 층 모델**입니다.
2차원 횡방향 퍼짐, 상부 공기층의 운동량 방정식, 에너지·상변화·액적·장애물은
해결하지 않습니다. 깊이평균 coupling을 구현했다는 사실을 SLAB/TWODEE의 전체
재구현·실험검증·현장 적합성으로 표현하지 않습니다. 결과와 영수증에도 연구 상태를
고정해 둡니다. 일반적인 시설 피해거리 산정용으로 승인한 모델이 아닙니다.

## 공개 근거 검토

- [Costa et al. (2008), shallow-layer heavy-gas model](https://doi.org/10.1029/2007GC001762):
  비정상 깊이평균 질량·농도·운동량 모델 계열의 공개 근거.
- [Chiapolino et al. (2021), two-layer heavy-gas equations](https://arxiv.org/abs/2101.04384):
  층 간 항·hyperbolicity·drag 검토가 필요하다는 근거. 논문의 2층 모델이나
  실험에서 정한 drag correlation을 그대로 구현하거나 계수로 가져오지 않았습니다.
- [Clawpack의 보존형 shallow-water/tracer 수치해법 문서](https://www.clawpack.org/v5.12.x/riemann/Shallow_water_Riemann_solvers.html):
  보존 변수·유량·유한체적 수치해법을 검토한 공개 참고입니다.

논문·코드·표·실험관측·매뉴얼은 저장하지 않았습니다. 아래 식과 수치해법은
명시한 제한 아래 자체 작성한 모델입니다. 위 논문의 완전한 지배방정식 또는
기관이 검증한 물성·closure로 표시하지 않습니다. 외부 독립평가는 수행하지 않았습니다.

## 방정식과 닫힘

각 cell의 바닥면적당 혼합물 질량 M [kg/m²], 방출물 질량 S [kg/m²], 수평운동량
P [kg/(m s)]를 저장합니다. constituent의 등온 밀도 rho_s와 rho_a는 입력입니다.
동일 온도·압력에서 부피가 가산된다고 가정합니다.

```text
h   = S/rho_s + (M-S)/rho_a
rho = M/h
u   = P/M
Pi  = g (rho-rho_a) h² / 2
    = g (1-rho_a/rho_s) S h / 2

dM/dt + d(M u)/dx           = source_mass + entrained_air
dS/dt + d(S u)/dx           = source_mass
dP/dt + d(P u + Pi)/dx      = source_momentum + air_momentum + wind_relaxation
```

질량분율이 고정되면 Pi는 M의 2차 함수이므로 파동속도는
`a²=2 Pi/M`、特性速度は `u-a, u, u+a`입니다.
실제로 이 3변수 flux Jacobian의 수치 고유값과 위 특성속도를 비교하는 시험을
포함합니다. 가벼운 성분을 dense로 취급하지 않도록 rho_s>rho_a를 요구합니다.
비Boussinesq 관성 M을 보존하지만 동적으로 움직이는 상부 공기층을 함께 푸는
2층 모델은 아닙니다. 상수 constituent 밀도·등온 부피가산 가정의 적용성은
물질·압력·온도별로 검토해야 합니다.

사용자 지정 entrainment 계수 alpha를 사용해 젖은 cell에
`rho_a alpha |U_wind-u|` kg/m²/s의 공기와 그 공기의 운동량을 넣습니다.
wind relaxation은 선택한 시간상수 tau로 `P→M U_wind`를 완화합니다.
이 두 closure는 검증된 현장 계수로 제공하지 않으며 alpha·tau·근거를 입력해야
합니다. tau=null이면 해당 항을 끕니다. source의 수평 주입속도도 명시적 입력입니다.
PRISM의 nozzle momentum·온도를 내부에서 임의로 추정하지 않습니다.

## 수치해법

첫 번째 차수 Rusanov 유한체적 flux를 사용합니다. 한 face의 flux를 양옆 cell에
반대 부호로 적용하므로 내부 이동은 전역 질량을 바꾸지 않습니다.
source/entrainment/relaxation과 flux는 1차 operator split입니다.
source를 넣은 trial state에서 파동속도를 계산하고 CFL 및 양수성을 만족할 때까지
dt를 줄입니다. CFL 입력은 최대 0.45입니다. source event와 output sample 시각에
dt를 정확히 맞춰 left-held 유량을 잘못 적분하지 않습니다.

임의의 구름 개수나 구간별 해의 합산은 없습니다. 같은 유량의 인접 interval을
합치므로 source 샘플링 구분 자체가 시간격자나 물리장을 바꾸지 않습니다.
first-order 수치확산이 있으며 정확한 front 도착시각·미세 shock 구조를 주장하지
않습니다. 건조 cell의 매우 작은 M에서는 u 계산에 1e-14 kg/m² guard를 사용하고
entrainment의 젖음 기준은 h>1e-12 m입니다. 질량을 dry cutoff로 제거하지 않습니다.

material 또는 ambient constituent 질량이 roundoff 허용 범위를 넘어 음수가 되면
dt를 재시도합니다. 허용 오차 내의 tiny correction은 signed ledger와 누적 절대
보정량에 기록합니다. 보정량이 최종 source 질량 기준 1e-9 한도를 넘으면 실패합니다.
보정 전후를 숨기거나 큰 음수 상태를 잘라 정상 결과로 승격하지 않습니다.
step budget·비유한 상태·CFL/양수성 retry 초과도 성공 결과를 반환하지 않습니다.

## 입력 계약과 PRISM 경계

기존 `ReleaseHistory`를 재사용하므로 원래 row/code digest·evidence·설비·시나리오·
운전 ID 및 ∑qΔt 검사는 유지됩니다. `history_from_prism_rows`를 통해 gas-only
left-held row를 입력할 수 있습니다. 액적/지면액체·질량분할 잔차는 계속 거부합니다.
기존 namespace/API를 바꾸지 않았으며 source 구간 수만큼 별도 solver를 실행하지 않습니다.

| 추가 입력 | 단위·제약 |
|---|---|
| temperature_k | source와 같은 K; 등온 경계 필수 |
| air_density_kg_m3, pure_vapour_density_kg_m3 | 동일 온도/압력의 constituent 밀도; pure>air>0 |
| density_basis, closure_basis | 밀도와 entrainment/drag 적용 근거 |
| x_min_m, x_max_m, cells | 증가 구간, 20..2000 cell |
| width_m, source_start_m | 고정 횡폭과 source rectangle의 시작 x |
| source.area_m2 | width×source length; 완전한 cell들에 정확히 정렬 |
| wind_speed_m_s, injection_velocity_m_s | 부호 있는 x 방향 속도 |
| wind_relaxation_time_s | >0 또는 null |
| entrainment_coefficient | 0..0.5, 명시적 입력 |
| gravity_m_s2 | >0 |
| maximum_step_s, cfl, maximum_steps | >0, CFL<=0.45, 기본 step budget 40000 |
| sample_times_s | 0부터 증가, 종료<=3600 s |
| receptors | 기존 ID/x/y/z, 최대32개; 고정 폭 밖은 미모델링으로 거부 |
| boundary | open_vacuum 또는 reflecting |
| applicability | research_1d_isothermal_fixed_width_flat_ground_layer 고정 |

source 면적의 일부만 cell에 걸치면 거부하며 면적을 조용히 늘리지 않습니다.
대기와 source 온도가 다르면 등온이라고 속여 실행하지 않습니다.
운영의 PRISM jet/LH2 이력을 ground/thermalized/isothermal 경계로 변환하는 것은
별도의 물리적 자격확인 단계입니다. 예제의 PRISM-shaped row는 새 합성 입력이며
실제 PRISM source 모델을 새로 실행했다는 의미가 아닙니다.

## 출력·질량수지·노출

`histories`와 `sample_times_s`를 기존 history-dose·probit·risk DAG에 연결합니다.
농도는 해당 cell의 **균일 수직층 내부** S/h kg/m³이며, receptor 높이가 층 위이면
0입니다. 체적분율은 (S/rho_s)/h입니다. 횡방향 Gaussian이나 기상 안정도별
폭 상관식을 추가하지 않았습니다. 고정 폭·균일층에서 나온 농도를 일반적인
3차원 점농도로 해석하지 않아야 합니다. 0높이의 얇은 수치적 front도 주의해야 합니다.

다음 시간 ledger와 최종 격자 상태를 반환합니다.

```text
방출물: 누적 주입 + signed roundoff = domain 방출물 + 경계 유출 방출물
혼합물: 누적 주입 + entrained air + signed roundoff
        = domain 혼합물 + 경계 유출 혼합물
```

open_vacuum은 외부 dry layer를 사용하고 양쪽의 유출 flux를 적분합니다.
reflecting은 바깥 face의 정상속도를 반사합니다. 외부 바람은 위 closure의 강제력이며
open boundary에서 임의의 오염물이나 공기를 다시 넣지 않습니다.
출력 ledger의 오차는 최종 source/entrainment 질량으로 정규화하며 허용값은 1e-8입니다.
추가로 최종 column 합이 domain 질량과 일치하고, 각 cell의 S<=M 및 부피/밀도
닫힘이 성립하는지 재검증합니다. 운동량 방정식을 풀지만 별도의 전역 운동량/에너지
검증 ledger를 제공한 것은 아닙니다.

영수증에는 기존 code/input/output hash와 evidence·주제 섹션·직접 출처를 보존하고,
`validation_level="research_numerical_tests"`, 출력에는
`model_status="research_numerically_verified_not_field_validated"`를 사용합니다.
NumPy 버전도 기록합니다. 현장 검증·표준 적합성 claim은 false입니다.

## 재현과 검증

```text
python -m pip install -e ".[test,coupled]"
python examples/ccps_coupled_layer.py --compare-independent --output artifacts/ccps-coupled.json
python -m pytest -q tests/test_ccps_coupled.py
```

합성 사례는 1 kg/s를 0..5 s와 8..13 s에 주입합니다. 동일 격자에서 두 펄스를
함께 계산한 해와, 각 펄스를 별도로 계산해 더한 해의 최종 species column 차이는
상대 L1 약 3.94%였습니다. 이는 solver가 독립 합산을 하지 않는다는 검증이지,
실험 대비 오차나 정확도 수치가 아닙니다.

14개 추가 시험은 질량·경계유출, flux consistency, Jacobian 파동속도,
quiescent reflecting symmetry, entrainment off, 결합/독립 차이, 동일 rate split
불변성, 100→200→400 cell의 상대 grid refinement, dt 세분화, 연속 공급,
잘못된 범위·budget·출력 조작, HTTP/DAG 및 PHA LOC→coupled→dose→합성 harm→risk를
확인합니다. grid 시험은 더 미세한 수치해에 대한 관측 수렴이며 exact/field 해를
입증하지 않습니다. 측정자료 검증·closure 보정·2차원 benchmark·상부 층·에너지
방정식은 추가 연구·검증 대상입니다.
