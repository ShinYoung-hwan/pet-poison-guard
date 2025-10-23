---
applyTo: '**'
---


# Pet Poison Guard — Copilot 지침서 (한국어, 최신화)

## 프로젝트 개요
Pet Poison Guard는 이미지 기반 AI 분석을 통해 반려동물에게 유해할 수 있는 음식/재료를 식별하고 관련 정보를 제공하는 서비스입니다. 시스템은 세 가지 주요 서비스로 구성됩니다:

- 프론트엔드: React + TypeScript (Vite)
- 백엔드: FastAPI 기반 REST API
- 데이터베이스: PostgreSQL(+pgvector)
- AI : PyTorch 기반 AI 서버

이 문서는 코드 자동 보조(에이전트/코파일럿)를 위한 개발 규칙, 아키텍처 요약, 통합 포인트와 운영·테스트 권장사항을 정리합니다.

## 아키텍처 및 데이터 흐름
- `ppg_frontend/` (React + Vite): 사용자 UI. 이미지 업로드, 분석 요청 전송, 결과 표시.
- `ppg_backend/` (FastAPI): 이미지 업로드 수신, 작업 생성/스케줄링, AI 서버/DB 연동, 결과 반환.
- `ppg_database/` (Postgres 17 + pgvector): 레시피/식품 데이터, 임베딩, 분석 결과 저장. Docker 초기화 스크립트 및 로드 스크립트로 데이터 적재.
- AI 서버: PyTorch 모델이 이미지/텍스트를 분석하여 유해도 및 관련 레시피를 반환. 백엔드에서 직접 호출하거나 작업 큐로 비동기 처리.

## 코드 관례 및 디렉터리 컨벤션

- 백엔드(`ppg_backend/app/`):
	- Pydantic 스키마 사용: `app/schemas/`
	- 기능별 구성: `app/api/`, `app/models/`, `app/services/`
	- 서비스 내부에 모델/스냅샷 보관: `app/services/snapshots/` (모델 가중치/임베딩, config 파일 등)
	- 비동기 작업/큐 관련: `app/services/queue_service.py`, `app/services/worker_service.py`

- 프론트엔드(`ppg_frontend/src/`):
	- 기능 기반 구조: `components/`, `pages/`, `services/`
	- API 호출은 중앙 서비스에서 관리: `src/services/api.ts`
	- 타입/도메인 모델: `src/models/AnalysisResult.ts`
	- 반복 폴링/비동기 업데이트: `src/services/usePolling.ts`

- 데이터베이스 및 데이터 초기화(`ppg_database/`):
	- 테이블 생성: `10_create_tables.sql`
	- 데이터 로드 스크립트: `20_load_tables.sh`, `load_tables.py`
	- 인덱스/성능 관련: `40_create_indexes.sql`

## 통합 포인트

- 프론트엔드 ↔ 백엔드: HTTP/JSON API. API 엔드포인트는 `ppg_backend/app/api/` 및 프론트엔드 `src/services/api.ts`에서 관리.
- 백엔드 ↔ AI 서버: `app/services/ai_service.py`를 통해 모델 추론 수행. 대용량/지연 작업은 작업 큐/비동기 워커로 처리.
- 백엔드 ↔ DB: 직접 SQL 또는 ORM을 사용하여 `ppg_database`에 적재된 데이터를 조회/저장.

## 외부 의존성(요약)

- 프론트엔드: Node.js(LTS 권장), Vite, React, Material-UI 등
- 백엔드: Python 3.12+ 권장, FastAPI, Pydantic, uvicorn, PyTorch(모델 추론이 필요한 경우)
- DB: PostgreSQL 17, pgvector 확장

## 개발·운영 권장사항

- 로컬 개발 환경
	- 프론트엔드: Node.js LTS(예: 18.x/20.x), `npm install` 또는 `pnpm` 사용
	- 백엔드: Python 3.12+ (프로젝트 요구사항은 `ppg_backend/requirements.txt` 참조)
	- DB: Docker로 PostgreSQL + pgvector 실행, 데이터 로드 스크립트 사용

- 배포/CI 권장
	- 프론트엔드: 타입 검사(tsc) → 린트(ESLint) → 유닛/통합 테스트(Jest)
	- 백엔드: 린트(ruff/flake8), 타입 검사(mypy 선택적), pytest 단위 테스트
	- PR 템플릿: 변경 범위, 테스트 결과, 로컬 재현 방법 포함

## 테스트 및 품질 관리

- 프론트엔드: React Testing Library + Jest 권장. 네트워크 종속성은 `msw`로 모킹.
- 백엔드: pytest 기반 유닛 테스트 (`ppg_backend/test/` 디렉터리)
- 정적 분석: ESLint(프론트엔드), ruff/flake8 및 mypy(백엔드 권장)

## 에이전트(코파일럿)용 팁

- 항상 `ppg_backend/app/services/snapshots/`에서 모델·데이터 파일을 확인하세요. 모델 파일이 없으면 테스트/로컬 추론이 실패합니다.
- 프론트엔드 API 변경 시 `ppg_frontend/src/models/`의 타입도 함께 업데이트하세요.
- 데이터 적재/스키마 변경은 `ppg_database/10_create_tables.sql` 및 `load_tables.py`를 동시에 수정하고, 마이그레이션/롤백 절차를 문서화하세요.
- 대규모 변경(데이터/모델 교체)은 코드 리뷰 및 수동 승인 필요 — 자동 PR 머지는 금지합니다.
- 사용자 질문에 대한 응답은 항상 한국어로 하세요. 단, 전문어는 영어로 표기할 수 있습니다. 단, 코드 내 주석과 commit 메시지는 영어로 작성하세요.

## 주요 참조 파일

- `ppg_frontend/README.md`
- `ppg_backend/README.md`
- `ppg_database/README.md`
- `ppg_backend/app/services/snapshots/` (모델·임베딩 파일)
- `ppg_frontend/src/services/api.ts`
- `ppg_frontend/src/models/AnalysisResult.ts`

## PR 체크리스트 (권장)

1. 관련 유닛 테스트가 추가/수정되었고 CI 통과
2. 타입 검사 및 린트 통과
3. 모델/데이터 파일 변경 시 `snapshots/`에 적절한 문서 또는 안내 포함
4. 보안·환경변수 변경 시 운영팀에 알림

---
간단 요약: 이 파일은 코파일럿/에이전트가 프로젝트 내부를 이해하고 안전하게 변경을 제안하도록 돕기 위한 가이드입니다. 변경하려는 경우 위의 관례와 PR 체크리스트를 따르세요.