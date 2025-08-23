---
applyTo: '**/ppg_frontend'
---

# Pet Poison Guard Frontend - Copilot Instructions

## 프로젝트 개요
Pet Poison Guard의 프론트엔드는 React 및 TypeScript 기반의 모바일 친화적 웹 앱입니다. 사용자는 반려동물에게 위험할 수 있는 음식의 이미지를 업로드하고, AI 분석 결과를 직관적으로 확인할 수 있습니다.

## 주요 요구사항
- React(TypeScript)로 개발합니다.
- 모바일 UI/UX를 우선적으로 고려합니다(반응형 디자인).
- 이미지 업로드, 결과 표시, 위험 식품 정보 제공 기능을 포함합니다.
- RESTful API를 통해 백엔드와 통신합니다.
- 다국어(한국어/영어) 지원을 고려합니다.
- 접근성(Accessibility)을 고려한 UI를 설계합니다.

## 코딩 가이드라인
- 코드 구조는 기능별로 폴더를 분리합니다(예: pages, components, services, models).
- 상태 관리는 React Context, Redux, 또는 React Query 등을 우선적으로 사용합니다.
- 네이밍은 영어로, 일관성 있게 작성합니다.
- 하드코딩된 문자열은 localization 처리합니다.
- UI는 Material-UI(MUI) 또는 유사한 컴포넌트 라이브러리를 사용합니다.
- API 통신 시 예외 처리를 반드시 구현합니다.
- 코드에 주석을 적절히 추가하여 가독성을 높입니다.

## 예시 폴더 구조