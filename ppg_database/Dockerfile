# 베이스 이미지로 PostgreSQL 17 및 pgvector 0.8.1 버전을 사용합니다.
FROM pgvector/pgvector:0.8.1-pg17-trixie

# --- 환경 설정 ---
# 데이터 파일들이 위치할 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# --- Python 설치 및 패키지 설치 ---
RUN apt update && apt upgrade -y \
    && apt install -y build-essential libpq-dev python3.13-venv python3-pip

# --- 가상 환경 생성 및 활성화 ---
# 1. /opt/venv 경로에 가상 환경 생성
RUN python3 -m venv /opt/venv

# 2. 컨테이너의 PATH 환경 변수에 가상 환경의 경로를 추가하여
#    이후의 모든 python, pip 명령어는 가상 환경의 것을 사용하도록 설정
ENV PATH="/opt/venv/bin:$PATH"

# 3. 이제 pip install은 보호 장치를 우회하지 않고 가상 환경 내부에 안전하게 설치됨
RUN pip install --no-cache-dir psycopg2-binary numpy tqdm

# PostgreSQL 서버가 8001 포트를 사용하도록 환경 변수를 설정합니다.
ENV PGPORT 8001

# --- 파일 복사 ---
# 호스트의 모든 data 파일들을 컨테이너의 /app/ 디렉토리로 복사합니다.
COPY ./*.pkl /app/
COPY ./*.json /app/
COPY ./load_tables.py /app/

# 초기화 스크립트인 create_tables.sql 파일을
# /docker-entrypoint-initdb.d/ 디렉토리로 복사합니다.
COPY ./10_create_tables.sql /docker-entrypoint-initdb.d/
COPY ./20_load_tables.sh /docker-entrypoint-initdb.d/

# --- 네트워크 설정 ---
# 컨테이너 외부에서 8001 포트로 접속할 수 있도록 설정합니다.
EXPOSE 8001

# 베이스 이미지의 기본 CMD가 postgres 서버를 실행하므로,
# 컨테이너가 시작되면 자동으로 8001 포트로 pgvector 서버가 실행되고
# create_tables.sql & load_tables.py 스크립트가 실행됩니다.