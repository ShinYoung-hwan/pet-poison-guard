---
applyTo: 'ppg_database/**'
---
## Pet Poison Guard Database 지침서

이 문서는 `ppg_database` 디렉토리의 구조와 운영 규칙을 소프트웨어 엔지니어가 빠르게 이해하고 동일한 작업 패턴을 따르도록 정리한 지침서다.

### 적용 범위

- 이 파일은 `ppg_database/**` 경로에 적용된다.

### 프로젝트 개요

- 이 디렉토리는 PostgreSQL 17과 `pgvector` 확장을 이용한 데이터베이스 이미지를 제공한다.
- 데이터 적재와 스키마 초기화는 도커 이미지의 초기화 스크립트로 자동화된다.

### 핵심 파일 목록 및 역할

- `Dockerfile` : 베이스 이미지 설정, Python 런타임과 의존성 설치, 데이터 및 초기화 스크립트 복사를 담당한다.
- `10_create_tables.sql` : 테이블 생성 및 `pgvector` 확장 설치 SQL 스크립트다.
- `20_load_tables.sh` : 컨테이너 시작 시 `load_tables.py`를 실행하도록 호출하는 쉘 스크립트다.
- `30_init_config.sh` : 초기 환경 설정과 권한 고정 등의 작업을 수행하는 스크립트다.
- `40_create_indexes.sql` : 성능을 위한 인덱스 생성 SQL 스크립트다.
- `load_tables.py` : JSON 및 PKL 파일을 읽어 데이터베이스에 적재하는 Python 스크립트다.
- `data/` 디렉토리 : 적재 대상 JSON 및 PKL 파일을 보관하는 디렉토리다.

### 빌드 및 실행 규칙

- 이미지 빌드는 프로젝트 루트의 `ppg_database` 디렉토리에서 수행한다.

```bash
docker build -t ppg_database .
```

- 컨테이너는 PostgreSQL 기본 포트 `5432`를 사용하도록 구성되어 있다.

```bash
docker run -d --name ppg_database \
	-e POSTGRES_PASSWORD=mysecretpassword \
	-e TZ=Asia/Seoul \
	-p 5432:5432 \
	-v db_data:/var/lib/postgresql/data \
	ppg_database
```

- 초기화 동작은 `/docker-entrypoint-initdb.d/`에 복사된 `*.sql` 및 `*.sh` 파일이 데이터 디렉토리가 비어있을 때만 실행되는 PostgreSQL 공식 이미지의 규칙을 따른다.
- 이미 초기화된 볼륨이 존재하면 스크립트가 재실행되지 않으므로 재적재가 필요하면 볼륨을 제거하고 재실행한다.

### 데이터 적재 및 코드 패턴 일관화

- 모든 데이터 적재 로직은 `load_tables.py` 하나를 통해 수행한다.
- `load_tables.py`는 `psycopg2`, `numpy` 등의 라이브러리를 사용하므로 Dockerfile에서 해당 라이브러리 설치를 유지해야 한다.
- 새로운 데이터 타입이나 테이블을 추가할 때는 다음 순서를 따른다.
	1. `10_create_tables.sql`에 새 테이블 정의를 추가한다.
	2. `load_tables.py`에 해당 테이블을 적재하는 로직을 추가한다.
	3. 필요한 데이터 파일을 `data/`에 추가하고 `Dockerfile`에 복사 지시를 추가한다.
	4. 이미지를 빌드하고 컨테이너를 재생성하여 동작을 확인한다.

### 환경 변수와 접속 정보

- 기본 DB 사용자명은 `postgres`다.
- 비밀번호는 컨테이너 실행 시 설정한 `POSTGRES_PASSWORD` 환경변수를 사용한다.
- 컨테이너 내부 PostgreSQL은 기본 포트 `5432`를 사용한다.

### 접속 및 검사 명령 예시

- 컨테이너 내부에서 `psql`로 접속하려면 다음을 실행한다.

```bash
docker exec -it ppg_database psql -U postgres -d postgres -p 5432
```

- 로컬에서 `psql` 클라이언트로 접속하려면 다음을 실행한다.

```bash
psql "host=localhost port=5432 user=postgres password=mysecretpassword dbname=postgres"
```

### 로깅 및 문제 해결

- 초기화 및 적재 진행 상황은 `docker logs ppg_database`로 확인한다.
- `load_tables.py` 실행 실패 시 다음을 확인한다.
	- `/app` 경로에 적재 대상 파일들이 존재하는지 확인한다.
	- Python 의존성이 정상적으로 설치되어 있는지 확인한다.
	- 스크립트에서 사용하는 DB 접속 정보가 컨테이너 내부 기준으로 올바른지 확인한다.
- 초기화 스크립트를 강제로 재실행하려면 기존 볼륨을 제거하고 컨테이너를 재생성한다.

### 운영 관행 및 개발자 규칙

- 데이터 변경은 SQL 스크립트(`10_create_tables.sql`, `40_create_indexes.sql`)와 `load_tables.py`를 동시에 업데이트해야 한다.
- 데이터 파일 추가 시 반드시 `data/`에 파일을 추가하고 `Dockerfile`에 `COPY` 지시문을 추가한다.
- 모든 변경 사항은 기능 단위로 커밋하고 PR을 통해 리뷰를 진행한다.
- 새로운 엔트리 포인트 스크립트나 의존성을 추가하면 `Dockerfile`과 `README.md`를 동기화하여 문서를 갱신한다.

### 통합 포인트

- 백엔드(`ppg_backend`)는 이 DB에 연결하여 레시피와 중독 데이터를 조회한다.
- 로컬 개발 환경에서는 백엔드가 `localhost:5432`로 연결되도록 설정한다.

### 권장 디버깅 워크플로우

1. 컨테이너 로그를 확인한다.

```bash
docker logs -f ppg_database
```

2. 컨테이너 내부로 진입하여 수동으로 스크립트를 실행해 본다.

```bash
docker exec -it ppg_database bash
cd /app
python3 load_tables.py
```

3. 문제가 재현되면 로그와 스택트레이스를 PR에 첨부하여 팀에 공유한다.
