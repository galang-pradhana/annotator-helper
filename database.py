import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from dotenv import load_dotenv

# Import models agar SQLModel.metadata terisi
import models 

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL harus di-set.")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# Setup engine async
engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    future=True,
    pool_pre_ping=True,      # Cek koneksi hidup sebelum pakai
    pool_recycle=1800,       # Recycle koneksi setiap 30 menit
    pool_size=20,            # Naikkan pool size awal
    max_overflow=30,         # Max tambahan koneksi jika pool penuh
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0
    }
)

# Membuat sessionmaker async
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """Membuat tabel. Metadata sudah terisi karena models di-import."""
    print("Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Database initialized.")

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager untuk session."""
    async with async_session_factory() as session:
        yield session
