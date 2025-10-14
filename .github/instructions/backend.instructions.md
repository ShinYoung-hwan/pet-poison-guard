---
applyTo: 'ppg_backend/**'
---

# Pet Poison Guard Backend - 개발 가이드 (한글)

이 문서는 현재 `ppg_backend` 디렉토리의 실제 구현을 반영한 백엔드 개발 지침서입니다. 엔드포인트, 비동기 작업 흐름, AI/DB 연동, 보안/테스트/린팅 권장사항을 한국어로 정리했습니다.

## 1. 개요
- 프레임워크: FastAPI (비동기 지원)
- 주 역할: 프론트엔드로부터 이미지 업로드 수신 → AI(이미지 임베딩) 분석 → DB(pgvector)에서 유사 레시피 탐색 → 독성 성분 매핑 → 결과 반환(비동기 작업 큐)

코드 구조(핵심 파일/모듈):
- `main.py`: FastAPI 앱 생성, lifespan에서 모델 로드, 라우터 등록, 글로벌 예외 처리
- `app/api/analyze.py`: `/api/analyze` (POST), `/api/task/{task_id}` (GET)
- `app/api/health.py`: `/api/health` (GET)
- `app/services/ai_service.py`: 모델 로드(`load_model()`), 이미지 → 임베딩(`image_to_embedding()`)
- `app/services/queue_service.py`: 비동기 분석 태스크 실행 및 AI 호출
- `app/services/task/task_service.py`: (현재) 인메모리 태스크 스토어 (생성/상태 업데이트/조회)
- `app/services/db_service.py`: pgvector 기반 유사도 조회 및 독성 매핑 함수
- `app/services/utils.py`: 설정 파일 로드 등 유틸

## 2. 공개 엔드포인트 (현행 구현 기준)
- POST /api/analyze
  - 입력: multipart/form-data 파일 필드 `file` (이미지)
  - 동작: 파일 사이즈/타입 검증, 태스크 생성, FastAPI `BackgroundTasks`에 `run_analysis_task` 예약
  - 응답: 202 Accepted, body: { "taskId": "<uuid>" }
  - 제한: MAX_FILE_SIZE = 5 * 1024 * 1024 (5MB), content_type 시작이 `image/` 이어야 함

- GET /api/task/{task_id}
  - 응답 모델: `TaskStatusResponse` (status: pending|completed|failed, data, detail)
  - 동작: `task_service.get_task()`로 조회, 완료 시 결과 포함

- GET /api/health
  - 간단한 헬스체크: { "status": "ok" }

참고: 프로젝트는 현재 BackgroundTasks + in-memory task store로 동작. 프로덕션에서는 Redis/큐(예: RQ, Celery, Dramatiq)와 영속적 상태 저장소(Redis/DB)를 권장합니다.

## 3. AI 서버 / 모델 연동 (요점)
- 앱 시작시(`main.py` lifespan) `ai_service.load_model()` 호출로 모델/디바이스 초기화.
- 이미지 임베딩 추출은 `ai_service.image_to_embedding(path)`를 통해 수행되며, 내부적으로 PIL + torchvision transform → 모델 추론 → numpy 반환.
- 모델 로드는 PyTorch checkpoint를 사용하고, CPU/GPU를 자동 선택.

권장사항
- 모델 로드 시 타임아웃/재시도/메모리 검사 로직을 추가하세요.
- 모델 파일 경로는 환경변수 또는 `ppg_backend/app/services/snapshots/config.json`에서 로드하도록 유지하세요.

## 4. DB 연동 및 벡터 검색
- `db_service.find_top_k_recipes(db, query_emb, top_k)`는 pgvector를 이용한 유사도 기반 쿼리를 수행합니다.
- `find_poisons_in_recipe`는 상위 레시피의 재료 문장에서 독성 항목을 문자열 매칭으로 추출합니다.

권장사항
- 문자열 매칭 방식은 간단하지만 한계가 있습니다. 정규화(소문자/띄어쓰기 제거) 및 다국어/동의어 처리를 고려하세요.
- 대규모 서비스의 경우 인덱스/파티셔닝, 캐싱(예: Redis) 고려.

## 5. 비동기 작업 흐름과 태스크 상태
- 현재 흐름:
 1) `/api/analyze`가 호출되면 `create_task()`로 UUID 생성 및 상태 pending 저장 (in-memory)
 2) BackgroundTasks에서 `run_analysis_task(task_id, file_tuple)` 실행
 3) `run_analysis_task`에서 임시파일에 이미지 저장 → `ai_service.image_to_embedding()` 호출 → DB에서 top-k 조회 및 poison 매핑 → `set_task_completed` 또는 `set_task_failed`

개선 권장
- 인메모리 스토어는 서버 재시작 시 사라집니다. Redis나 DB 기반 상태 저장으로 전환하세요.
- 작업 큐를 분리(워커 프로세스)하면 API 서버가 블로킹되지 않습니다.

## 6. 입력 검증 및 보안 (구체)
- 파일 타입: `Content-Type`이 `image/*`인지 확인
- 파일 크기: 5MB 제한 (현재 `analyze.py`의 MAX_FILE_SIZE)
- 파일 내용 검증: 확장자/메타데이터보다 실제 바이너리 검사(예: Pillow로 열기)로 안전성 검증 권장
- 에러 메시지: 내부 예외(스택트레이스 등)는 노출하지 말고 일반화된 메시지 사용(예: "Internal server error")
- 업로드 디렉토리: 임시파일 사용 시 권한/cleanup 계획 수립

## 7. 로깅·모니터링
- 로깅 레벨 사용: INFO / WARNING / ERROR
- 중요한 이벤트(모델 로드 성공/실패, 태스크 실패, DB 에러)는 로그에 남기되 민감정보는 마스킹
- 요청/응답 메트릭, 태스크 처리 시간, DB 쿼리 시간 등을 수집해 모니터링(예: Prometheus) 권장

## 8. 테스트 전략
- 유닛 테스트: 개별 서비스(ai_service, db_service, task_service 등)의 핵심 로직을 테스트
- 통합 테스트: API 엔드포인트를 TestClient로 호출하되, AI/DB는 목(mock)으로 대체
- 성능 테스트: `test/performance/`에 있는 locust 파일 및 벤치마크 스크립트 활용

테스트 작성 원칙(요점)
- 독립성: 테스트는 서로 의존하지 않음
- 격리: 외부 의존(모델, DB)은 모킹
- 경계조건: 빈 파일, 큰 파일(허용/초과), 비이미지 바이트 등

## 9. 코드 스타일·정적분석
- 타입 힌트: 모든 공개 함수/메서드에 타입 힌트 권장
- Docstring: 각 함수/클래스는 목적·입력·출력·예외·사용 예시를 포함
- 린터/타입체크: ruff, flake8, mypy 사용 권장. pre-commit 훅에 등록 권장

예시 Docstring 스타일
```python
from typing import List
def sum_numbers(numbers: List[int]) -> int:
	"""
	주어진 정수 리스트의 합을 반환합니다.

	Args:
		numbers (list[int]): 합산할 정수 리스트

	Returns:
		int: 리스트의 합

	Examples:
		>>> sum_numbers([1,2,3])
		6
	"""
	return sum(numbers)
```

## 10. 배포/런타임 고려사항
- `main.py`의 lifespan 훅에서 모델을 로드하므로 컨테이너 시작 시 모델 로드 시간이 필요합니다. (이미지 크기/모델 크기에 따라 수십초 이상 소요 가능, 현재 모델은 1초 미만)
- Docker 환경에서는 모델 파일 경로 및 메모리(GPU) 설정을 확인하세요.

Note: 개발 및 로컬 실행을 위한 가상환경 경로는 반드시 `ppg_backend/.venv` 로 설정해 주세요. 이 경로를 사용하면 문서의 예제 명령과 프로젝트 설정이 일관되게 동작합니다.

중요: 백엔드 관련 모든 실행(예: 가상환경 생성/활성화, 의존성 설치, 테스트 실행, 서버 시작 명령 등)은 항상 `ppg_backend` 디렉토리에서 실행해야 합니다. 예를 들어, 프로젝트 루트에서 작업 중인 경우 다음과 같이 이동한 후 명령을 실행하세요:

```
cd ppg_backend
# 이후 명령 실행 (예: .venv 생성/활성화, pip install -r requirements.txt, pytest 등)
```

## 11. 마이그레이션 및 개선 아이디어 (단기·중기)
- 단기: 태스크 저장소를 Redis로 전환, BackgroundTasks → 외부 워커로 이동
- 중기: AI 추론을 별도의 모델서버(예: TorchServe, Triton)로 분리
- 장기: 멀티 모델/버전 관리, A/B 테스트, 모델 성능 모니터링

## 12. 빠른 체크리스트 (PR 검토 시)
- 변경한 함수/클래스에 docstring과 타입 힌트가 있는가?
- 입력 검증(파일 타입/크기)과 오류 응답이 적절한가?
- 외부 호출은 추상화되어 목킹 가능한가?
- 테스트(유닛 또는 통합)가 추가되었는가? 핵심 경로는 커버되는가?
- 린트/타입 체크가 통과하는가?

## 13 Backend Python 코드 작성 원칙

다음은 이 저장소의 백엔드(Python/FastAPI) 코드를 작성할 때 반드시 따라야 할 세부 원칙입니다. 기존 문서의 전반적 규칙과 충돌하지 않도록 상세화한 내용이며, 코드 품질과 유지보수성을 높이기 위해 적용합니다.

- 모든 함수와 클래스에는 목적, 입력(매개변수), 출력(반환값), 예외 상황, 사용 예시를 포함한 docstring을 작성할 것.
- 타입 힌트(type hints)를 모든 함수 인자와 반환값에 명시할 것. (예: def foo(x: int) -> str)
- 입력 검증과 에러 처리는 함수 내부에서 명확히 다룰 것. 외부 요청 데이터는 Pydantic 스키마로 검증하고, 서비스/유틸 함수에는 명확한 타입 서명을 추가할 것.
- 함수·클래스명, 변수명은 명확하고 일관된 네이밍 규칙을 따를 것(예: snake_case for functions/variables, PascalCase for classes).
- 복잡한 로직은 작은 단위의 함수로 분리하고 재사용 가능한 유틸리티로 모을 것. 중복을 줄이고 테스트 가능한 단위로 구성할 것.
- 비동기(Async) I/O 경로는 async/await 스타일을 사용하고, 동기 코드와 혼용할 때는 명확하게 분리할 것.
- 외부 호출(예: AI 서버, DB, 외부 API)은 가능한 한 추상화하고, 테스트 시에는 목(mock) 또는 페이크(fakes)를 통해 격리할 것.
- 로깅은 적절한 레벨(INFO, WARNING, ERROR)을 사용해 중요한 이벤트와 오류를 기록할 것. 민감한 정보(토큰, 비밀번호 등)는 로그에 남기지 말 것.
- 보안 고려: 입력값(특히 파일 업로드)은 사이즈/타입 제한을 두고 검사할 것. 반환 메시지는 내부 정보가 노출되지 않도록 일반화된 오류를 사용.
- 테스트: 각 공개 엔드포인트와 핵심 서비스 함수에 대해 단위 및 통합 테스트를 작성할 것. AI 서버 등 외부 의존은 목(mock)으로 대체하여 독립적으로 실행 가능해야 함.
- 예외 처리 정책: 예측 가능한 오류는 커스텀 예외로 정의하고 적절한 HTTP 상태 코드로 매핑하여 응답할 것. Uncaught 예외는 글로벌 에러 핸들러에서 잡아 500으로 응답하되, 내부 로그에는 상세 스택트레이스를 남길 것.
- 타입/정적 분석: mypy, ruff/flake8 같은 도구를 도입해 정적 타입 검사와 린팅을 수행할 것(가능하면 pre-commit 훅으로 자동화).
- Docstring 예시 및 스타일: Google/Numpy 스타일 또는 reStructuredText 중 하나를 프로젝트 내에서 통일하여 사용하고, docstring에 간단한 usage 예시(작은 코드 블록)를 포함할 것.
- 경계조건·에지케이스: 빈 입력, 최대/최소 파일 크기, 비정상적 바이너리 데이터 등 경계 조건을 테스트에 포함할 것.
- 변경 시 회고: 기능 수정이나 버그 수정 시, 어떤 입력/프롬프트가 문제를 유발했는지 간단한 회고를 작성하고, 개선된 프롬프트(또는 재현 스텝)를 커밋 메시지 또는 PR 설명에 포함할 것.

예시 스니펫(권장 스타일):

```python
from typing import List, Optional

def sum_numbers(numbers: List[int]) -> int:
	"""
	주어진 정수 리스트의 합을 반환합니다.

	Args:
		numbers (List[int]): 합산할 정수 리스트
	Returns:
		int: 리스트의 모든 원소의 합

	Examples:
		>>> sum_numbers([1, 2, 3])
		6
	"""
	return sum(numbers)
```