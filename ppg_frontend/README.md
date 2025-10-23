# Pet Poison Guard Frontend

이 문서는 `ppg_frontend` 애플리케이션을 로컬 또는 도커 환경에서 문제없이 실행하기 위한 엔지니어용 가이드이다. 모든 설명은 실행 가능한 단계 중심으로 작성되었다.

## 개요

`ppg_frontend`는 React + TypeScript 기반의 모바일 친화적 웹 애플리케이션이다. 사용자는 음식 이미지를 업로드하고 백엔드의 AI 분석 결과를 확인하며, 위험 식품 정보를 열람할 수 있다. 다국어(한국어/영어)를 지원한다.

## 시스템 요구사항

- Node.js LTS (권장: 18.x 이상) 또는 호환되는 Node 버전을 사용한다.
- npm 또는 pnpm/yarn 중 하나를 사용한다.
- Docker(선택사항): 컨테이너 실행을 원하면 Docker와 Docker Compose를 설치한다.

## 폴더 구조 (요약)

```
ppg_frontend/
├── Dockerfile
├── eslint.config.js
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── public/
└── src/
		├── assets/
		├── components/
		├── locales/    # en.json, ko.json
		├── models/     # AnalysisResult.ts
		├── pages/
		└── services/   # api.ts, usePolling.ts
```

## 빠른 시작 — 로컬 개발

1) 저장소 루트에서 `ppg_frontend` 디렉터리로 이동한다.

2) 의존성 설치

```bash
npm install
```


3) 개발 서버 실행

```bash
npm run dev
```

4) 브라우저에서 `http://localhost:5173` 또는 출력된 Vite 주소로 접속한다.

참고: 애플리케이션이 백엔드 API와 통신하려면 환경변수 또는 `src/services/api.ts`의 설정이 올바르게 되어 있어야 한다. `vite.config.ts`를 확인해 API 주소를 변경해준다.

## 프로덕션 빌드 및 정적 파일

프로덕션 빌드를 생성하려면 다음을 실행한다.

```bash
npm run build
```

생성된 정적 파일은 `dist/` 디렉터리에 생성된다. `dist/`의 내용을 NGINX 또는 정적 호스팅 서비스로 서빙한다.

## Docker 빌드 및 실행

이미지를 빌드하고 컨테이너로 실행하려면 다음을 사용한다.

1) Docker 이미지 빌드

```bash
docker build -t ppg_frontend .
```

2) 컨테이너 실행 (포트 80에 매핑)

```bash
docker run -d --name ppg_frontend -p 80:80 ppg_frontend
```

참고: Docker로 구동할 때는 백엔드 컨테이너와 동일 네트워크에 연결한다.

## 테스트 및 정적 분석

- 단위 테스트는 React Testing Library + Jest를 권장한다. 테스트가 아직 추가되어 있지 않으면 우선 핵심 컴포넌트에 대한 스캐폴딩 테스트를 추가한다.
- 린트 검사와 타입 검증을 실행한다.

```bash
npm run lint
```
<!-- TODO : make type-check feature -->
<!-- TODO : make type-check & lint CI -->
<!-- npm run type-check  -->

`package.json`에 해당 스크립트가 없으면 간단히 추가한다.

## 주요 파일 설명

- `src/main.tsx` — 애플리케이션 진입점이다.
- `src/App.tsx` — 라우팅 및 상위 레이아웃 컴포넌트이다.
- `src/pages/UploadPage.tsx` — 이미지 업로드와 분석 요청 흐름을 구현한 페이지이다.
- `src/components/ImageUpload.tsx` — 이미지 업로드 UI 컴포넌트이다.
- `src/services/api.ts` — 백엔드와의 HTTP 통신을 중앙에서 관리하는 파일이다.
- `src/models/AnalysisResult.ts` — 백엔드 분석 결과 타입 정의 파일이다.

## 배포 관련 유의사항

- 정적 파일은 `dist/`에서 제공하므로 CDN 또는 NGINX를 통해 캐싱 정책을 적절히 설정한다.
- 환경별 설정은 빌드 시점에 주입하거나 런타임 구성(service worker, reverse proxy)를 사용해 관리한다.

## 자주 발생하는 문제와 해결법

- 개발 서버에서 API 호출이 실패한다면 `API_BASE_URL`이 올바른지 확인한다.
- CORS 오류가 발생하면 백엔드의 CORS 설정을 확인한다.
- 포트 충돌이 발생하면 Vite 또는 Docker 실행 시 다른 포트를 지정한다.

## 추가 권장 작업

- 유닛 테스트와 E2E(Playwright) 테스트를 추가해 업로드→분석 플로우를 자동 검증한다.
- 이미지 업로드 전 클라이언트 측 압축/리사이즈를 적용해 업로드 시간을 단축한다.
- CI 파이프라인에 `type-check`, `lint`, `test`, `build` 단계를 추가한다.
