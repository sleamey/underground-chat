import asyncio
from asyncio import StreamReader, StreamWriter

import configargparse
import logging
import json


def create_argparser():
    p = configargparse.ArgParser(
        default_config_files=['~/.minechat'],
        description="Connects to chat as specified user (or creates a new one) and posts given message. "
        "NOTE: When attempt to login with provided token is successful nickname is ignored."
    )
    p.add('message', help="Message to send to chat")
    p.add('--host', '-H', default="minechat.dvmn.org", env_var="CHAT_HOST", help="Host to connect to")
    p.add('--port', '-p', default=5050, type=int, env_var="CHAT_PORT", help="Port to listen")
    p.add('--token', '-t', env_var='CHAT_TOKEN', help="Path to chat log")
    p.add('--nickname', '-n',  env_var='CHAT_NICKNAME', help="Nickname to create user with")
    p.add('--debug-log', '-d', action='store_true', env_var='CHAT_DEBUG_LOG', help="Turn on verbose debug logging")
    return p


def sanitize_text(msg):
    return " ".join(msg.split("\n"))


async def connect(host: str, port: int) -> (StreamReader, StreamWriter):
    reader, writer = await asyncio.open_connection(host, port)
    return reader, writer


async def disconnect(writer: StreamWriter):
    writer.close()
    await writer.wait_closed()


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

    await receive_data(reader)  # Получаем приветствие пользователя, после этого можно отправлять сообщения
    return user_object


async def register(reader: StreamReader, writer: StreamWriter, nickname):
    await receive_data(reader)  # Получаем приветственное сообщение
    await send_data(writer, "")  # Пропускаем логин по токену

    await receive_data(reader)  # Получаем запрос имени
    await send_data(writer, f"{sanitize_text(nickname)}\n")

    user_str = await receive_data(reader)
    user_object = json.loads(user_str)
    print(f"Welcome, {user_object['nickname']}, your token is {user_object['nickname']} ")

    await receive_data(reader)  # Получаем приветствие пользователя
    return user_object


async def submit_message(reader: StreamReader, writer: StreamWriter, message):
    await send_data(writer, f"{sanitize_text(message)}\n")
    await receive_data(reader)  # Получаем подтверждение отправки


async def main():
    arguments = create_argparser().parse_args()

    log_level = logging.DEBUG if arguments.debug_logging else logging.WARNING
    logging.basicConfig(format="%(levelname)-8s [%(asctime)s] %(message)s", level=log_level)

    user = None
    reader, writer = await connect(arguments.host, arguments.port)
    if arguments.token:
        user = await authorize(reader, writer, arguments.token)
    if not user:
        if not arguments.nickname:
            print("You have to provide nickname in order to register a user")
            await disconnect(writer)
            exit(-1)
        await register(reader, writer, arguments.nickname)

    await submit_message(reader, writer, arguments.message)


if __name__ == '__main__':
    asyncio.run(main())