# 한국어 사용자 안내

배포명은 **process-risk-consequence-toolkit**, 기존 Python import는
`ccps_consequence`입니다. CCPS/AIChE의 공식 제품이 아니며 호환성 식별자를
유지한 독립 프로젝트입니다. 원문·표·그림·예제답·외부 엔진 소스는 배포하지 않습니다.

## 상세 모듈·파라미터 찾기

[23개 모듈 전체 색인](MODULES.md)에서 각 계산을 클릭하면 **모든 입력과 출력**,
필수/기본값, enum, 단위, 범위, 근거와 시험 위치를 확인할 수 있습니다.
중첩된 source/context/history/branch 필드는 [공통 모델](REFERENCE_MODELS.md)에
모두 기록했습니다. 자동 생성한 표의 기준은 실제 Python 모델과 JSON Schema입니다.
영어 설명과 실제 필드명을 같이 유지해 다른 도구도 동일 계약을 사용하게 했습니다.

## 설치·실행

```text
python -m pip install process-risk-consequence-toolkit
python -m pip install "process-risk-consequence-toolkit[http,coupled,dense]"
prct catalog
prct schema --calculation source/liquid
prct workflow examples/ccps_screening.workflow.json
prct serve
```

기본 설치는 Pydantic만 사용합니다. coupled는 NumPy, dense는 별도 SLABx1.0.8,
http는 FastAPI/Uvicorn을 추가합니다. CLI 결과는 JSON이고 실패는 stderr와
종료코드2로 구분합니다. HTTP 기본 주소는127.0.0.1:8765이며 `/docs`에서 시험할
수 있습니다. 공용 운영 서버로 배포하는 보안·사용자 관리 기능은 포함하지 않습니다.

## 모델 선택

- 방출원: 액체/기체 단공, 재고 제한, 현열 flash, 입력 증발 flux의 질량수지.
- 수동 확산: Gaussian plume/puff. sigma를 입력하며 dense 모델로 자동 전환하지 않습니다.
- 고밀도 순간 방출: 실제 SLABx puff와 자체 수용점 재구성.
- 연속·유한시간: 일정 구간의 native plume-to-puff, 명시적 성장 구름/독립 합성 근사.
- 결합 모델: 하나의 격자에서 질량·방출물·운동량을 같이 계산하는 연구용1D 등온·고정 폭 모델.
- 화재·폭발: 공개 근거의 한정된 screening 식. 상세 jet 형상이나 임의 과압 곡선을 모두 제공하지 않습니다.
- 노출·위험: 정규화 dose, 입력 probit 계수, LOC 빈도와 분기·추가 인자의 위험기여도.

[순간 dense](CCPS_DENSE_HISTORY.md), [방출 이력](CCPS_RELEASE_HISTORY.md),
[결합 모델](CCPS_COUPLED_LAYER.md), [공개 계산 확장](CCPS_PUBLIC_MODEL_EXPANSION.md)에
식·가정·실패조건을 자세히 정리했습니다. 이전 host PHA용 설명은 역사적 호스트
연동 맥락이며, standalone 배포의 명령/HTTP 계약은 MANUAL.md가 기준입니다.

## 단위와 근거

압력은 Pa 절대압, 온도 K, 시간 s, 질량 kg입니다. native 물성의 분자량은
**kg/mol**입니다. 섭씨·게이지압·kg/kmol을 그대로 넣지 않아야 합니다.
NaN/Inf, 숫자 문자열, bool, 음수와 불필요한 필드는 거부합니다.
applicability·phase·basis 등의 선언은 모델 가정과 입력 근거이지 프로그램이
자동으로 현장 적용성을 승인하는 기능이 아닙니다.

Context의 설비·시나리오·운전 ID, evidence 참조, source/code hash를 유지합니다.
영수증은 입력/출력/코드 해시와 한계를 기록하며 `verify_receipt`로 재계산합니다.
source/workflow/receipt/environment를 함께 보관해야 합니다.

## 통합과 검증

FTA/LOPA/SIL은 외부 PHA의 LOC 빈도로 연결합니다. API-581은 명시적 release
receipt, PRISM은 gas-only left-held 이력·근거 경계로 연결하며 원본 코드·데이터를
동봉하지 않습니다. [연동 문서](INTEGRATIONS.md)를 참고하세요.

시험은 합성 해석해·보존·수렴·계약·실제 선택형 엔진 실행을 구분합니다.
현장 검증·안전 인증·CCPS 표준 적합성을 뜻하지 않습니다. portable 배포본의
실제 시험 결과는 [검증 보고서](../verification/VALIDATION.md)가 기준입니다.
개발 재개는 [AGENTS.md](../AGENTS.md), [개발 인수인계](DEVELOPMENT.md),
[구현 이력](IMPLEMENTATION_HISTORY.md)을 먼저 읽으세요.
