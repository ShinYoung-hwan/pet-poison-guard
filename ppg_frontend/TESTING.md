# 테스트 가이드 — Pet Poison Guard (ppg_frontend)

이 문서는 `ppg_frontend`의 테스트 작성 · 실행 · 유지보수 방법을 한국어로 정리한 문서입니다. 현재 프로젝트에 추가된 테스트 설정, 로컬 실행 방법, CI 동작, 그리고 PR 관련 체크리스트를 포함합니다.

## 목표

- UI 컴포넌트와 서비스에 대해 신뢰할 수 있는 단위(Unit) 및 통합(Integration) 테스트를 제공
- 통합 테스트에서 네트워크 의존을 제거하기 위해 `msw` 사용
- CI에서 타입 검사와 테스트를 실행하고 커버리지 아티팩트를 업로드하도록 구성
- 접근성(a11y) 및 로컬라이제이션(한국어) 동작을 검증

## 테스트 파일 구조 (요약)

- `src/__tests__/test-utils.tsx` — React Testing Library용 커스텀 렌더러
- `src/setupTests.ts` — 전역 테스트 설정(jest-dom, matchMedia 폴리필, TextEncoder 폴리필, msw 초기화 자리)
- `src/components/__tests__/` — 컴포넌트 단위 테스트 (예: ImageUpload, ResultDisplay, PoisonResultList)
- `src/services/__tests__/` — 서비스 단위/통합 테스트(추가 예정)
- `test/fixtures/` — (예정) 테스트용 샘플 이미지 및 픽스처

## 테스트 유형

- 단위(Unit) 테스트: 개별 컴포넌트나 훅(hook) 동작 검증 (Jest + React Testing Library)
- 통합(Integration) 테스트: HTTP 엔드포인트를 `msw`로 모킹하여 백엔드에 실제 요청을 보내지 않음 (`/api/analyze`, `/api/task/:id` 등)
- E2E(옵션): Playwright로 업로드 → 분석 → 결과 플로우를 스테이징 환경에서 검증

## 테스트 유틸 사용법

- `render`는 `src/__tests__/test-utils.tsx`에서 제공하며 기본적으로 `MemoryRouter`로 래핑되어 있습니다. 사용 예:

```ts
import { render, screen } from '../__tests__/test-utils';
```

- 테마(ThemeProvider), i18n, React Query 등이 필요한 컴포넌트의 경우 커스텀 렌더러에 해당 Provider를 추가하세요.

## 로컬에서 테스트 실행하기

의존성 설치 (프로젝트 루트 또는 `ppg_frontend`):

```bash
cd ppg_frontend
npm ci
# 또는 lockfile이 없을 경우
npm install
```

테스트 실행:

```bash
# 전체 테스트 실행
npm test

# 단일 테스트 파일 실행
npx jest src/components/__tests__/ImageUpload.test.tsx --runInBand --verbose
```

타입 검사 및 린트:

```bash
npm run type-check
npm run lint
```

커버리지 생성(설정에 따라):

```bash
# Jest에서 커버리지를 생성하여 coverage/에 출력
npm run coverage
```

## CI 관련 노트

- 워크플로우: `.github/workflows/frontend-ci.yml` (push, pull_request, 수동 트리거 지원)
- 주요 단계: 의존성 설치( `ppg_frontend/package-lock.json` 사용) → 타입 검사 → 린트(현재 CI에서 주석 처리됨) → 단위/통합 테스트 → `coverage/` 아티팩트 업로드
- `actions/setup-node`에 `cache-dependency-path: ./ppg_frontend/package-lock.json`을 지정해 `ppg_frontend` 내부의 lockfile을 사용하도록 구성했습니다.
- E2E를 활성화하려면 레포지토리 시크릿 `STAGING_URL`을 등록하고 워크플로우를 수동 트리거할 때 `run_e2e=true`로 실행하세요.

## 테스트 작성 시 체크리스트

테스트를 추가할 때 다음을 지키세요:

- 적절한 디렉토리(`src/components/__tests__` 또는 `src/services/__tests__`)에 파일 추가
- 외부 모듈(예: `api.uploadImage`)은 순수 단위 테스트에서 `jest.mock()`으로 모킹
- HTTP 통합 테스트는 `msw` 핸들러로 응답을 정의하여 실제 API 호출을 피함
- React Testing Library의 `screen` 쿼리(`getByRole`, `getByLabelText`, `findBy*`)를 우선 사용 — 접근성 쿼리 권장
- `jest.useFakeTimers()`는 필요한 경우에만 사용하고 테스트 후 복원
- 비동기 UI 업데이트는 `waitFor` / `findBy`를 사용(고정 대기시간 사용 금지)
- UI 문자열은 한국어 로컬라이제이션에 따라 테스트

## 접근성(a11y)

- `a11y.test.tsx`를 추가하여 `axe-core`로 주요 페이지/컴포넌트 스캔 수행
- `critical`이나 `serious` 이슈는 병합 금지, `minor`는 이후 트래킹

## PR 체크리스트 (테스트 관련)

- [ ] 새 UI 동작에 대한 단위 테스트(정상 경로) 포함
- [ ] 에러 상태 및 엣지 케이스 커버
- [ ] 변경하는 엔드포인트에 대해 msw 통합 테스트 추가(해당되는 경우)
- [ ] 새 인터랙티브 컴포넌트에 대한 접근성 스모크 테스트 포함
- [ ] CI (type-check, tests, coverage) 통과

## 향후 작업(우선순위)

- `msw` 통합 테스트 추가: `src/services/__tests__/api.integration.test.ts` 및 `src/setupTests.ts`에서 msw 서버 시작/종료 설정
- 테스트 픽스처 추가: `test/fixtures/images/`에 샘플 이미지 추가
- `axe-core` 기반 a11y 테스트 추가
