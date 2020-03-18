import asyncio
from asyncio import StreamReader, StreamWriter

from aiofiles import open
import datetime
import configargparse
import logging
import json

account_hash = "00ffa302-6932-11ea-b989-0242ac110002"

logging.basicConfig(format="%(levelname)-8s [%(asctime)s] %(message)s", level=logging.DEBUG)


def create_argparser():
    p = configargparse.ArgParser(default_config_files=['~/.minechat'])
    p.add('--host', default="minechat.dvmn.org", env_var="CHAT_HOST", help='Host to connect to')
    p.add('--port', default=5050, type=int, env_var="CHAT_PORT", help='Port to listen')
    p.add('--token', default="00ffa302-6932-11ea-b989-0242ac110002",
          env_var="CHAT_TOKEN", help='Path to chat log')
    return p


async def connect(host: str, port: int) -> (StreamReader, StreamWriter):
    reader, writer = await asyncio.open_connection(host, port)
    return reader, writer


async def send_data(writer: StreamWriter, msg: str):
    writer.write(f"{msg}\n".encode())
    await writer.drain()
    logging.debug(f":sent:{msg}")


async def receive_data(reader: StreamReader) -> str:
    msg = (await reader.readline()).decode()
    logging.debug(f":received:{msg}")
    return msg


async def authorize(reader: StreamReader, writer: StreamWriter, token: str) -> dict:
    _ = await receive_data(reader)  # Получаем приветственное сообщение

    await send_data(writer, f"{token}\n")

    user_str = await receive_data(reader)
    user_object = json.loads(user_str)
    if not user_object:
        print("Неизвестный токен. Проверьте его или зарегистрируйте заново.")
    else:
        print(f"Добро пожаловать, {user_object['nickname']}")

    await receive_data(reader)  # Получаем приветствие пользователя
    return user_object


async def register(reader: StreamReader, writer: StreamWriter, nickname):
    await receive_data(reader)  # Получаем приветственное сообщение
    await send_data(writer, "")  # Пропускаем логин по токену

    await receive_data(reader)  # Получаем запрос имени
    await send_data(writer, f"{nickname}\n")

    user_str = await receive_data(reader)
    user_object = json.loads(user_str)
    print(f"Добро пожаловать, {user_object['nickname']}")

    await receive_data(reader)  # Получаем приветствие пользователя
    return user_object


async def submit_message(reader: StreamReader, writer: StreamWriter, message):
    await send_data(writer, f"{message}\n")
    await receive_data(reader)  # Получаем подтверждение отправки


async def main():
    arguments = create_argparser().parse_args()
    reader, writer = await connect(arguments.host, arguments.port)
    user = await register(reader, writer, 'sleevney')
    await submit_message(reader, writer, "Всем привет!")
    writer.close()
    await writer.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
