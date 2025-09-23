

# Pet Poison Guard Database (ppg_database)

이 디렉토리는 Pet Poison Guard 프로젝트의 PostgreSQL + pgvector 데이터베이스 초기화 및 데이터 적재를 위한 공간입니다.

## 주요 파일
- `Dockerfile` : PostgreSQL 17 + pgvector 환경 및 Python 패키지 설치
- `layer1.json`, `layer2.json`, `layer2+.json` : 레시피 데이터
- `petpoison_data.json` : 애완동물 중독 정보 데이터
- `rec_embeds.pkl`, `rec_ids.pkl` : 레시피 임베딩 및 ID

- `load_tables.py` : json/pkl 데이터를 DB에 적재하는 Python 스크립트
- `10_create_tables.sql` : DB 테이블 및 pgvector 확장 생성
- `20_load_tables.sh` : 컨테이너 내에서 load_tables.py 실행용 쉘 스크립트

## 빌드 및 실행 방법

1. **이미지 빌드**
    ```bash
    docker build -t ppg_database .
    ```

2. **컨테이너 실행**
    ```bash
    docker run -d --name ppg_database \
        -e POSTGRES_PASSWORD=mysecretpassword \
        -e TZ=Asia/Seoul \
        -p 5432:5432 \
        -v db_data:/var/lib/postgresql/data  
        ppg_database  
    ```


3. **테이블 생성 및 데이터 적재 (자동 실행)**
    - 컨테이너가 시작되면 `/docker-entrypoint-initdb.d/10_create_tables.sql`로 테이블 생성과 `/docker-entrypoint-initdb.d/20_load_tables.sh`를 통한 데이터 적재가 모두 자동으로 실행됩니다.
    - 별도의 명령 없이 컨테이너 실행만으로 모든 데이터가 적재됩니다.
    - 완료 여부는 아래 명령으로 로그를 확인하세요:
    ```bash
    docker logs ppg_database
    ```

## DB 접속 예시

컨테이너 내부에서 psql로 접속:
```bash
docker exec -it ppg_database psql -U postgres -d postgres -p 8001
```

## 참고
- DB 포트: 8001
- 기본 DB명/유저: postgres
- 비밀번호: mysecretpassword (환경변수로 설정)