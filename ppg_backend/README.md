# Pet Poison Guard Backend

이 디렉터리는 Pet Poison Guard의 FastAPI 기반 백엔드 서비스입니다.

## 주요 기능
- 이미지 업로드 및 분석 API 제공
- AI 서버와 연동하여 반려동물 유해 식품 판별
- RESTful API 및 OpenAPI 문서 지원

## 설치 방법 

### 공통

- `ppg_backend/app/services/snapshots/config.json`에 `model_path` 경로 수정

### Docker로 설치

1. 이미지를 빌드합니다.
    ```sh
    docker build -t ppg_backend .
    ```
2. 컨테이너를 `ppg_backend` 이름으로 실행합니다.
    ```sh
    docker run --name ppg_backend -p 8000:8000 ppg_backend
    ```

### Docker 없이 직접 설치

1. Python 3.13 이상이 설치되어 있는지 확인하세요.
2. 가상환경을 생성하고 활성화합니다.
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   ```
3. 필요한 패키지를 설치합니다.
   ```sh
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## 실행 방법

1. FastAPI 서버 실행
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
2. API 문서는 [http://localhost:8000/docs](http://localhost:8000/docs)에서 확인할 수 있습니다.

## 참고
- AI 모델 및 데이터 파일은 `app/services/snapshots/`에 위치해야 합니다.
- 데이터베이스가 필요한 경우, 상위 디렉터리의 README를 참고하세요.

## 개발 및 테스트
- 테스트 코드는 `test/`에 위치합니다.
- 테스트 실행:
   ```sh
   pytest app/test/
   ```
