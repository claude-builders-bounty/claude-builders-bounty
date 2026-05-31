import asyncio
import traceback

async def safe_run(coro):
    try:
        return await coro
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}