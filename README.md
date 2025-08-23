# 이미지 기반 반려동물 위해 식품 식별 및 분석 - PET Poison Guard

## Introduction

- Pet Poison Guard는 반려동물의 안전을 위해 설계된 애플리케이션입니다.
- 이 애플리케이션은 이미지를 기반으로 반려동물에게 위험이 될 수 있는 유해 식품을 감지하고 사용자가 반려동물의 건강을 지킬 수 있도록 돕습니다.

## 기능

- **유해 물질 데이터베이스**: 반려동물에게 위험한 물질에 대한 정보를 제공합니다.
- **이미지 기반 위해 식품 식별 및 분석**: 음식 이미지를 기반으로 반려동물에게 위험한 식품인지 식별하고, 왜 위험한지 분석합니다.

```mermaid
graph TD
    subgraph "사용자 영역"
        User["👨‍💻 사용자"]
    end

    subgraph "서비스 인프라 (로컬 환경)"
        Frontend["📱 React<br>모바일 UI 웹"]
        Backend["⚙️ FastAPI<br>백엔드 서버"]
        TaskQueue["📨 비동기 작업 큐<br>"]
        AIServer["🤖 PyTorch<br>AI 서버 (멀티모달 전용)"]
    end

    %% 데이터 흐름 정의
    User -- "앱 사용 (모바일/데스크탑)" --> Frontend
    
    Frontend -- "API 요청 (HTTP/S)" --> Backend
    Backend -- "JSON 응답" --> Frontend
    
    Backend -- "<b>멀티모달 기능 요청</b><br>(이미지, 텍스트 등)" --> TaskQueue
    TaskQueue -- "작업 전달 (FIFO)" --> AIServer
    
    AIServer -- "결과 반환<br>(Webhook 또는 결과 큐)" --> Backend
    
    subgraph "내부 처리 로직"
      direction LR
      Backend_Logic["백엔드 일반 로직<br>(DB CRUD, 인증 등)"]
      AI_Processing["AI 연산<br>(GPU/CPU 자원 활용)"]
      
      Backend --- Backend_Logic
      AIServer --- AI_Processing
    end

    %% 스타일링
    style User fill:#d4e4ff,stroke:#333,stroke-width:2px
    style Frontend fill:#c1f0f0,stroke:#333,stroke-width:2px
    style Backend fill:#f9d5e5,stroke:#333,stroke-width:2px
    style TaskQueue fill:#fdebd0,stroke:#333,stroke-width:2px
    style AIServer fill:#e8dff5,stroke:#333,stroke-width:2px
```


## 설치 방법

1. 이 저장소를 클론합니다.
   ```bash
   git clone https://github.com/ShinYoung-hwan/pet-poison-guard.git
   ```
2. 필요한 패키지를 설치합니다.
   ```bash
   cd pet-poison-guard/backend
   pip install -r requirements.txt
   ```
3. 데이터베이스를 설정합니다.
   ```bash
   # 데이터베이스 초기화 명령어
   ```

## 사용 방법

1. 서버를 실행합니다.
   ```bash
   uvicorn main:app --reload
   ```
2. 웹 브라우저에서 `http://localhost:8000`에 접속합니다.

## 기여 방법

기여를 원하시는 분은 이슈를 생성하거나 Pull Request를 제출해 주세요.

## 기술 스택

- **프론트엔드**: React
- **백엔드**: FastAPI
- **데이터베이스**: SQLAlchemy

## 라이센스

## 연락처

- 이메일: shinefilm1@gmail.com
- GitHub: [Young-Hwan Shin](https://github.com/ShinYoung-hwan)
