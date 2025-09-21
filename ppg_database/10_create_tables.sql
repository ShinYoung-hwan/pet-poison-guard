-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 레시피 데이터 테이블 생성
CREATE TABLE recipe_data (
    id TEXT PRIMARY KEY,
    data JSONB
);

-- 벡터 임베딩 테이블 생성
CREATE TABLE rec_embeds (
    id TEXT PRIMARY KEY,
    embedding vector(1024)
);

-- 애완동물 중독 정보 테이블 생성
CREATE TABLE pet_poisons (
    id SERIAL PRIMARY KEY,
    name TEXT,
    alternate_names TEXT[],
    poison_description TEXT,
    desktop_thumb TEXT
);