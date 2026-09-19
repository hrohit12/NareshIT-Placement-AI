from ai_job_agent import run_job_search
import asyncio

async def test():
    await run_job_search("Python Developer", "San Francisco")

asyncio.run(test())
