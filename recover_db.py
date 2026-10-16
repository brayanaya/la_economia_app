import asyncio
from app.db.session import engine
from app.core.database import Base
from app.main import app
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
