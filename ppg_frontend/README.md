# Pet Poison Guard Frontend

React 기반 반려동물 음식 위험 분석 웹앱의 프론트엔드입니다. 모바일 친화적 UI, 이미지 업로드, AI 분석 결과 표시, 다국어 지원(한국어/영어)을 제공합니다.

## 폴더 구조

```
ppg_frontend/
├── Dockerfile
├── eslint.config.js
├── index.html
├── package.json
├── README.md
├── tsconfig.app.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── public/
├── src/
│   ├── App.css
│   ├── App.tsx
│   ├── index.css
│   ├── main.tsx
│   ├── vite-env.d.ts
│   ├── assets/
│   │   └── ppg.png
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── ImageUpload.tsx
│   │   ├── PoisonResultList.tsx
│   │   └── ResultDisplay.tsx
│   ├── locales/
│   │   ├── en.json
│   │   └── ko.json
│   ├── models/
│   │   └── AnalysisResult.ts
│   ├── pages/
│   │   ├── DescriptionPage.tsx
│   │   ├── HomePage.tsx
│   │   ├── IntroPage.tsx
│   │   └── UploadPage.tsx
│   └── services/
│       ├── api.ts
│       └── usePolling.ts
```

## 주요 기능
- 음식 이미지 업로드 및 AI 분석 결과 표시
- 위험 식품 정보 제공
- 다국어 지원 (한국어/영어)
- 모바일/반응형 UI
- RESTful API 연동

## 실행 방법

### 1. 로컬 개발 환경 (비 Docker)

#### 1) 의존성 설치
```bash
npm install
```

#### 2) 개발 서버 실행
```bash
npm run dev
```

#### 3) 접속
브라우저에서 [http://localhost](http://localhost) 접속  
또는 docker-compose를 사용하는 경우 [http://localhost:8080](http://localhost:8080) 접속

> **백엔드 API 주소 변경:**
> 기본적으로 `src/services/api.ts`에서 API 주소를 설정합니다. 백엔드가 다른 포트/호스트에서 실행 중이면 해당 파일을 수정하세요.

### 2. Docker 환경

#### 1) 이미지 빌드
```bash
docker build -t ppg_frontend .
```

#### 2) 컨테이너 실행
```bash
docker run -d --name ppg_frontend -p 80:80 ppg_frontend
```

#### 3) 접속
브라우저에서 [http://localhost:5173](http://localhost:5173) 접속

> **API 연동:**
Docker로 실행 시, 백엔드 컨테이너와 네트워크 연결이 필요합니다. API 주소를 환경에 맞게 수정하세요.

## 환경 변수 및 설정
- API 서버 주소: `src/services/api.ts`에서 직접 수정
- 다국어: `src/locales/en.json`, `src/locales/ko.json`에서 텍스트 관리

## 빌드
```bash
npm run build
```
`dist/` 폴더에 정적 파일이 생성됩니다.

## 기타
- ESLint, TypeScript, Vite 기반
- Material-UI(MUI) 사용
- 접근성(Accessibility) 고려

## 문의
이슈 및 문의는 저장소 Issue 탭을 이용해 주세요.
