import os
import logging
from typing import List, Dict, Any
from sqlalchemy import String, Text, DateTime, func, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logger = logging.getLogger("Database")

# Reads from environment variable first; defaults to standard local dev setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/scraper_db"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ScrapedItemModel(Base):
    __tablename__ = "scraped_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    price: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


async def init_db():
    """Create tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_scraped_items(items: List[Dict[str, Any]]) -> int:
    """Upsert scraped items directly into PostgreSQL."""
    async with AsyncSessionLocal() as session:
        saved_count = 0
        for item_data in items:
            stmt = select(ScrapedItemModel).where(ScrapedItemModel.url == item_data["url"])
            result = await session.execute(stmt)
            existing_item = result.scalar_one_or_none()

            if existing_item:
                existing_item.title = item_data["title"]
                existing_item.price = item_data.get("price")
                existing_item.meta_description = item_data.get("meta_description")
            else:
                new_item = ScrapedItemModel(
                    url=item_data["url"],
                    title=item_data["title"],
                    price=item_data.get("price"),
                    meta_description=item_data.get("meta_description"),
                )
                session.add(new_item)
            saved_count += 1

        await session.commit()
        return saved_count
