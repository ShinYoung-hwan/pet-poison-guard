from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os

DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'mysecretpassword')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# TODO: write logs to file
engine = create_async_engine(
    DATABASE_URL, 
    echo=False
    )
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
# TODO: use async session if needed
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session