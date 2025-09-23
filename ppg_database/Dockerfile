# TODO: buffer size 늘려서 40s을 1s 이하로 줄일 것!

# 베이스 이미지로 PostgreSQL 17 및 pgvector 0.8.1 버전을 사용합니다.
FROM pgvector/pgvector:0.8.1-pg17-trixie

# --- 환경 설정 ---
# 데이터 파일들이 위치할 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

#

# --- Python 설치 및 패키지 설치 및 가상 환경 생성 ---
RUN apt update && apt upgrade -y \
    && apt install -y python3.13 python3-pip \
    && pip3 install --break-system-packages --no-cache-dir \
    pgvector \
    asyncpg \
    numpy \
    tqdm

#     PostgreSQL 서버가 5432 포트를 사용하도록 환경 변수를 설정한다.
ENV PGPORT=5432

# --- 파일 복사 ---
# 호스트의 모든 data 파일들을 컨테이너의 /app/ 디렉토리로 복사한다.
COPY ./data/* /app/
COPY ./load_tables.py /app/

# 초기화 스크립트인 create_tables.sql 파일을
# /docker-entrypoint-initdb.d/ 디렉토리로 복사합니다.
COPY ./10_create_tables.sql /docker-entrypoint-initdb.d/
COPY ./20_load_tables.sh /docker-entrypoint-initdb.d/
COPY ./30_init_config.sh /docker-entrypoint-initdb.d/

# --- 네트워크 설정 ---
# 컨테이너 외부에서 5432 포트로 접속할 수 있도록 설정합니다.
EXPOSE 5432

# 베이스 이미지의 기본 CMD가 postgres 서버를 실행하므로,
# 컨테이너가 시작되면 자동으로 5432 포트로 pgvector 서버가 실행되고
# create_tables.sql & load_tables.py 스크립트가 실행됩니다.