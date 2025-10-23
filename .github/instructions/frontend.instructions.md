---
applyTo: 'ppg_frontend/**'
---

# Pet Poison Guard Frontend - Copilot Instructions

## 프로젝트 개요
Pet Poison Guard의 프론트엔드는 React 및 TypeScript 기반의 모바일 친화적 웹 애플리케이션이다. 사용자는 음식 이미지를 업로드해 백엔드의 AI 분석을 받아보고, 분석 결과와 위험 식품 정보를 손쉽게 확인할 수 있도록 설계되었다.

## 주요 요구사항
 - React(TypeScript)로 개발한다.
 - 모바일 UI/UX를 우선적으로 고려한다(반응형 디자인).
 - 이미지 업로드, 결과 표시, 위험 식품 정보 제공 기능을 포함한다.
 - RESTful API를 통해 백엔드와 통신한다.
 - 다국어(한국어/영어) 지원을 고려한다.
 - 접근성(Accessibility)을 고려한 UI를 설계한다.

추가 목표 (Engineer-facing):
 - 안전하고 예측 가능한 개발 경험을 제공하기 위해 타입 안전성(TypeScript), 유닛/통합 테스트, 정적 분석을 기준으로 삼는다.
 - 자동화된 빌드/배포(CI) 파이프라인을 가정하고, 환경별 설정(env)을 분리한다.

## 코딩 가이드라인
 - 코드 구조는 기능별로 폴더를 분리한다(예: pages, components, services, models).
 - 상태 관리는 React Context, Redux, 또는 React Query 등을 우선적으로 사용한다.
 - 네이밍은 영어로, 일관성 있게 작성한다.
 - 하드코딩된 문자열은 localization 처리한다.
 - UI는 Material-UI(MUI) 또는 유사한 컴포넌트 라이브러리를 사용한다.
 - API 통신 시 예외 처리를 반드시 구현한다.
 - 코드에 주석을 적절히 추가하여 가독성을 높인다.

세부 규칙(실무 적용 가능한 항목):


- TypeScript 설정
	- 엄격 모드(strict)를 유지한다. 프로젝트 `tsconfig.json` 기본값을 따르되, 새 파일을 추가할 때는 가능한 한 정확한 타입을 선언한다.
	- 공용 모델은 `src/models/`에 배치한다. 예: `AnalysisResult.ts`는 API 응답 타입의 단일 소스이다.


- 컴포넌트 작성
	- 기능(Feature)-기반 디렉터리 구조를 권장한다: `components/`, `pages/`, `services/`, `models/`, `locales/`.
	- 프레젠테이션 컴포넌트(무상태)는 가능한 한 순수함수로 작성하고, 로직은 훅(hooks) 또는 서비스로 분리한다.
	- 스타일은 CSS 모듈 또는 스타일드 컴포넌트를 사용한다. 기존 코드의 `App.css` 스타일 규칙을 존중한다.


- 상태 관리
	- 로컬 상태는 `useState`/`useReducer`, 전역 상태는 React Context 또는 React Query로 관리한다. 큰 비동기 로직(분석 요청)은 React Query(또는 SWR)로 처리하여 캐싱/재시도 전략을 사용한다.


- API 통신
	- `src/services/api.ts`에서 모든 HTTP 클라이언트를 중앙 집중화한다. 에러/타임아웃 처리, 재시도 정책, 전역 로딩 상태 관리를 구현한다.
	- 민감한 설정(예: API URL)은 빌드환경변수(.env)를 사용한다. `VITE_` 접두사를 사용한다.


- 에러 처리
	- 사용자에게 친절한 오류 메시지를 표시하고, 분석 실패 시 재시도/보고 경로를 제공한다.


- 접근성(Accessibility)
	- 모든 이미지 업로드/결과 화면은 적절한 aria-속성, 키보드 내비게이션, 색 대비를 갖춘다.
	- 파일 입력 컨트롤에는 레이블을 명시적으로 연결한다.


- 로컬라이제이션
	- `src/locales/en.json` 및 `src/locales/ko.json`을 사용해 모든 사용자 문구를 관리한다. 하드코딩 문자열은 금지한다.

작성 스타일 가이드
 - 함수/컴포넌트 명명은 동사형 또는 명사형으로 일관성 있게 사용(예: `UploadPage`, `ImageUploader`).
 - 커밋 메시지는 Conventional Commits 스타일을 권장한다.

## 실제 폴더 구조 (2025년 9월 기준)
```
ppg_frontend/
	eslint.config.js
	index.html
	package.json
	README.md
	tsconfig.app.json
	tsconfig.json
	tsconfig.node.json
	vite.config.ts
	public/
	src/
		App.css
		App.tsx
		index.css
		main.tsx
		vite-env.d.ts
		assets/
			ppg.png
		components/
			Header.tsx
			ImageUpload.tsx
			PoisonResultList.tsx
			ResultDisplay.tsx
		locales/
			en.json
			ko.json
		models/
			AnalysisResult.ts
		pages/
			DescriptionPage.tsx
			HomePage.tsx
			IntroPage.tsx
			UploadPage.tsx
		services/
			api.ts
			usePolling.ts

```

## 개발 환경 및 빠른 시작

1) 요구 도구
 - Node.js LTS (권장: 18.x 이상), npm 또는 pnpm/yarn
 - Vite 개발 서버


2) 로컬 실행
 - 종속성 설치
	- npm
		- npm install
	- pnpm
		- pnpm install

 - 개발 서버
	- npm run dev

3) 빌드
 - npm run build

4) 간단한 환경 구성
 - `.env.local` 또는 `.env`에 `VITE_API_BASE_URL` 같은 값을 설정한다.

## 테스트와 품질 보증


- 테스트
	- 유닛 테스트: React Testing Library + Jest를 권장한다.
	- 기존 repo에 테스트 스크립트가 없다면 `npm run test` 명령을 추가하고 `src/components`와 `src/services`에 핵심 유닛 테스트를 작성한다.


- 정적 분석
	- ESLint(프로젝트에 `eslint.config.js` 존재), Prettier를 사용해 일관된 코드 스타일을 유지한다.
	- CI에서 `npm run lint`와 `npm run type-check`를 실행한다.

## CI/CD 제안


- 기본 파이프라인(예: GitHub Actions)
	- 체크아웃, Node 설치, 의존성 설치
	- 타입 검사(tsc --noEmit)
	- 린트 검사(eslint)
	- 유닛 테스트
	- 빌드(생성산물 업로드 또는 Docker 이미지 빌드)

## 보안과 비밀 관리


- 민감정보(토큰, 비밀키)은 리포지토리에 커밋하지 않는다. CI에 비밀을 등록하고 런타임 환경변수를 통해 주입한다.

## 운영/배포


- Docker
	- `ppg_frontend/Dockerfile`과 `nginx.conf`가 이미 제공되어 있다. 프로덕션 이미지는 `npm run build` 출력물을 NGINX로 서빙하도록 구성되어 있다.

## 성능 유의사항


- 이미지 업로드
	- 프런트엔드에서 업로드 전에 클라이언트 측 축소/압축(가능하면 WebP 변환)을 고려한다.
- 번들 사이징
	- 코드 스플리팅(라우트 기반), 압축, 캐싱 헤더를 이용해 초기 로드 타임을 줄인다.

## 협업 및 컨벤션


- 브랜치 전략
	- 기능(feature/*) / 버그fix(hotfix/*) / 릴리스(release/*) 등 명명 규칙을 따른다.
	- PR 체크리스트
	- 변경 범위, 타입 검사 통과, 린트/테스트 통과, 로컬 빌드 확인, 문서 업데이트(필요 시)

## 코드 에이전트(자동화/봇)을 위한 지침

목표: 코드 에이전트가 이 파일을 읽고 일관성 있고 유지보수 가능한 React 코드를 생성하도록 구체적 규칙과 체크리스트를 제공한다.

### 에이전트 계약(Contract)
- 입력: 변경 대상(컴포넌트/페이지) 이름과 목적, 관련 API 모델(예: `AnalysisResult`), 환경변수(예: `VITE_API_BASE_URL`), 그리고 원하는 스타일/테스트 요구사항을 제공한다.
- 출력: TypeScript 컴포넌트(.tsx), 스타일 파일(.module.css 또는 styled component), 관련 테스트(.test.tsx), 필요시 서비스/모델 업데이트를 생성한다.
- 오류 모드: 타입 검사 실패, 테스트 실패, 린트 오류 등이 발생하면 반드시 브랜치를 생성하고 PR을 통해 변경을 제출한다. 실패 원인을 PR에 상세히 기재한다.

### 에이전트 동작 원칙(핵심)
1. 단일 책임 원칙(SRP)을 지킨다: 컴포넌트는 하나의 책임만 갖게 하고, 복잡한 로직은 커스텀 훅이나 유틸리티로 분리한다.
2. 타입 안정성을 보장한다: 모든 Props와 중요한 함수에는 명시적 TypeScript 타입을 추가한다. 공용 타입은 `src/models/`에 둔다.
3. 컴포넌트 패턴을 사용한다: 컴파운드 컴포넌트 또는 제네릭 컴포넌트 패턴을 적용해 재사용성을 높인다.
4. Hooks 규칙을 따른다: `useEffect`는 부수 효과에만 사용하고 cleanup을 구현한다. 비용이 큰 계산은 `useMemo`로, 자식에 전달하는 콜백은 `useCallback`으로 메모이제이션한다.
5. 접근성(ARIA), 로컬라이제이션, 테스트를 항상 포함한다: 새로운 UI는 적절한 ARIA 속성, 로컬라이제이션 키, 그리고 최소한의 유닛 테스트를 포함한다.
6. 변경 범위가 클 경우 사람 승인을 요청한다: 파일 삭제, 아키텍처 전환, 외부 라이브러리 교체 등은 반드시 PR에서 리뷰어 승인을 받는다.

### 구현 세부 규칙
- 파일/디렉터리 위치
	- 컴포넌트는 기능별 디렉터리에 위치시킨다(예: `src/features/upload/components/ImageUpload.tsx`).
	- 공용 컴포넌트는 `src/components/` 또는 `src/shared/components/`에 둔다.
	- 타입은 `src/models/`에 둔다.

- 네이밍
	- 컴포넌트: PascalCase를 사용한다.
	- 훅: `use` 접두사로 시작한다(e.g., `useImageUpload`).
	- 이벤트 핸들러: `handle` 접두사, Props 핸들러: `on` 접두사 사용한다.

- 컴포넌트 구현
	- 프레젠테이션 컴포넌트는 가능한 한 무상태로 작성하고, 로직은 훅이나 서비스로 위임한다.
	- 스타일은 CSS 모듈(`*.module.css`) 또는 styled-components를 사용한다(프로젝트 규칙에 따른다).

- 타입 및 API
	- 새 API 응답 모델을 추가하면 `src/models/`에 타입을 정의하고 `src/services/api.ts`의 관련 함수에 반영한다.
	- 런타임 유효성 검사를 위해 Zod 같은 스키마를 도입할 것을 권장한다.

- 테스트
	- 모든 새 UI에는 최소한 한 개의 유닛 테스트를 추가한다(React Testing Library 권장).
	- 비동기 로직은 가짜 서버(msw) 또는 mocking을 사용해 테스트한다.

### 성능 및 안정성
- 비용이 큰 연산은 `useMemo`로 감싼다.
- 콜백은 `useCallback`으로 메모이제이션한다.
- 리스트 렌더링 시 `key`를 명확히 지정한다.

### Error handling
- UI 수준의 예외는 Error Boundary를 사용해 캡처하고 사용자에게 친화적인 폴백 UI를 제공한다.
- 네트워크/비즈니스 오류는 서비스 레이어에서 통합 로그를 남기고, 사용자에게 적절한 재시도 옵션을 제공한다.

### 프롬프트 및 PR 작성 규칙
- 변경 내용 설명에는 다음을 포함한다: 무엇을 변경했는지, 왜 변경했는지, 관련 파일 목록, 타입 검사/테스트 결과 요약을 포함한다.
- 에이전트는 자동 생성한 코드를 커밋하기 전에 `npm run type-check`와 `npm run lint`를 실행해 사전 검증을 수행한다.

### 체크리스트(에이전트가 PR 생성 시 따라야 할 최소 항목)
- 타입 검사 통과이다.
- 린트 규칙 통과이다.
- 관련 유닛 테스트가 존재하고 통과한다.
- 로컬라이제이션 키가 추가되었으면 `src/locales/`에 반영되었다.
- 접근성(ARIA)이 적용되었다.

## 변경/삭제 정책


- 중요한 원칙: 이 문서에 적힌 기존 규칙이나 파일(예: `locales`, `models`, `services`)을 삭제하거나 대체하려면 사람의 승인을 받아야 한다. 에이전트는 자동으로 중요한 파일을 삭제하지 않도록 설계되어야 한다.

## 참고: 현재 주요 파일


- `src/main.tsx` — 앱 엔트리
- `src/App.tsx` — 라우터/상위 레이아웃
- `src/pages/UploadPage.tsx` — 업로드 페이지(이미지 입력 + 분석 요청 흐름)
- `src/components/ImageUpload.tsx` — 업로드 UI
- `src/services/api.ts` — 백엔드 통신 중앙화
- `src/models/AnalysisResult.ts` — 분석 결과 타입

## 추가 권장 작업 (Proactive extras)


- 테스트 스캐폴딩: 주요 컴포넌트에 대해 기본 유닛 테스트와 일부 통합 테스트를 추가한다.
- E2E: Playwright 또는 Cypress로 업로드 흐름의 E2E 테스트를 추가한다.

---

유의사항: 원문에 있던 핵심 내용(구조/요구사항)은 보존했다. 삭제하거나 크게 변경해야 하는 내용이 있으면 우선 승인을 요청한다.