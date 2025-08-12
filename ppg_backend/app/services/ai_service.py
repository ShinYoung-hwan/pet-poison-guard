import os
import httpx

AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:8001/analyze")

async def request_ai_analysis(file: tuple, timeout: float = 15.0) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            AI_SERVER_URL,
            files={"file": file}
        )
    response.raise_for_status()
    return response.json()
