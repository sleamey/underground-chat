from contextlib import asynccontextmanager
import asyncio
from asyncio import StreamReader, StreamWriter

from typing import AsyncContextManager


@asynccontextmanager
async def get_chat_connection(host: str, port: int) -> AsyncContextManager[(StreamReader, StreamWriter)]:
    reader, writer = await asyncio.open_connection(host, port)
    try:
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()

