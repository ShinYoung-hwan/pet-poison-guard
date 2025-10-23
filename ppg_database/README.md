# Pet Poison Guard Database (ppg_database)

이 문서는 Pet Poison Guard 프로젝트의 PostgreSQL 17 + pgvector 데이터베이스를 로컬에서 빠르게 빌드하고 초기화하는 절차를 설명한다.

## 핵심 요약

- 이 이미지는 `pgvector/pgvector:0.8.1-pg17-trixie`를 기반으로 PostgreSQL 17과 필요한 Python 패키지를 설치하도록 구성되어 있다.
- 컨테이너는 내부적으로 PostgreSQL 서버를 5432 포트로 실행하도록 설정되어 있다.
- 데이터 적재 및 스키마 생성은 `/docker-entrypoint-initdb.d/`에 복사된 스크립트들(`10_create_tables.sql`, `20_load_tables.sh`, `30_init_config.sh`, `40_create_indexes.sql`)에 의해 컨테이너 최초 기동시 자동으로 실행된다.

## 주요 파일 및 역할

- `Dockerfile` : 베이스 이미지, Python 패키지 설치, 데이터 및 초기화 스크립트 복사를 담당한다.
- `10_create_tables.sql` : DB 테이블 및 `pgvector` 확장 생성 SQL 스크립트다.
- `20_load_tables.sh` : 컨테이너 내부에서 `load_tables.py`를 실행하는 쉘 스크립트다.
- `load_tables.py` : JSON 및 PKL 파일에서 데이터를 읽어 DB에 적재하는 Python 스크립트다.
- `30_init_config.sh` : 초기 구성 스크립트다.
- `40_create_indexes.sql` : 인덱스 생성 스크립트다.
- `data/` : 적재에 필요한 JSON 및 PKL 데이터 파일들이 위치한 디렉토리다.

## 빌드 절차

1) data 준비

    - layer1.json : Recipe1M+ 데이터셋에서 다운로드 한다. (데이터베이스 공개 정책에 따라서 [Recipe1m+ Dataset Access](https://forms.gle/EzYSu8j3D1LJzVbR8)에서 신청해야만 한다.)
    - rec_ids.pkl, rec_embeds.pkl : [im2recipe-Pytorch](https://github.com/torralba-lab/im2recipe-Pytorch) 프로젝트의 test.py를 실행시켜서 생성한다.
    - petpoison_data.json : 위험 식품 데이터 셋을 자체적으로 생성한다. (기본적으로는 [Pet Poison Helpline](https://www.petpoisonhelpline.com/)의 데이터베이스를 따른다.)


2) 도커 이미지 빌드

```bash
docker build -t ppg_database .
```

## 컨테이너 실행 절차

1) 기본 실행 명령은 다음과 같다.

```bash
docker run -d --name ppg_database \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e TZ=Asia/Seoul \
  -p 5432:5432 \
  -v db_data:/var/lib/postgresql/data \
  ppg_database
```

2) 설명:

- `POSTGRES_PASSWORD` 환경변수로 루트 비밀번호를 설정한다.
- 로컬 호스트의 `5432` 포트를 컨테이너의 `5432` 포트로 매핑한다.
- 데이터 영속화는 `-v db_data:/var/lib/postgresql/data` 볼륨으로 수행한다.

## 자동 초기화 동작

- PostgreSQL 공식 이미지의 초기화 동작을 따라 `/docker-entrypoint-initdb.d/`에 위치한 모든 `*.sql` 및 `*.sh` 파일은 데이터 디렉토리가 비어있을 때만 실행된다.
- 따라서 기존 볼륨에 데이터가 남아있는 경우에는 초기화 스크립트가 재실행되지 않는다.
- 초기화 스크립트를 다시 실행하려면 기존 볼륨을 제거하거나 새로운 볼륨을 사용한다.

```bash
# 기존 볼륨을 제거하고 컨테이너와 볼륨을 재생성하는 예시다.
docker rm -f ppg_database || true
docker volume rm db_data || true
docker run -d --name ppg_database -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -v db_data:/var/lib/postgresql/data ppg_database
```

## 로그 확인 및 진행 상태 확인 방법

- 컨테이너 로그를 확인하여 스키마 생성 및 데이터 적재 진행 상태를 확인한다.

```bash
docker logs -f ppg_database
```

- 로드 스크립트는 `load_tables.py`가 출력하는 로그와 함께 실행되므로 에러가 발생하면 해당 로그를 통해 원인을 파악한다.

## DB 접속 예시

- 컨테이너 내부에서 `psql`로 접속하려면 다음을 실행한다.

```bash
docker exec -it ppg_database psql -U postgres -d postgres -p 5432
```

- 로컬에서 `psql` 클라이언트를 이용해 직접 접속하려면 다음을 실행한다.

```bash
psql "host=localhost port=5432 user=postgres password=mysecretpassword dbname=postgres"
```

## 문제 해결 팁

- 컨테이너가 시작되었으나 초기화가 되지 않는다면 데이터 볼륨이 비어있는지 확인한다.
- 초기화 스크립트가 실행되지 않는 일반적 원인은 이미 초기화된 데이터 디렉토리가 존재하기 때문이다.
- 데이터 재적재가 필요하면 기존 볼륨을 삭제한 뒤 컨테이너를 재생성한다.
- `load_tables.py`가 실패하면 Python 의존성 설치 상태와 데이터 파일의 존재 여부를 확인한다.
- 컨테이너 내부에서 수동으로 스크립트를 실행해 문제를 재현하려면 `docker exec -it ppg_database bash`로 진입 후 `/app/load_tables.py`를 직접 실행한다.

## 참고 정보

- 컨테이너 내부에서 PostgreSQL은 기본적으로 포트 `5432`를 사용한다.
- 기본 DB 사용자명은 `postgres`이며 비밀번호는 `POSTGRES_PASSWORD` 환경변수로 설정한 값이다.
- 제공된 스크립트와 데이터 파일은 `/app` 경로에 복사되어 있다.
