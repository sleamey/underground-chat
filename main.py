import asyncio
from aiofiles import open
import datetime
import configargparse


def create_argparser():
    p = configargparse.ArgParser(default_config_files=['~/.underchat'])
    p.add('--host', default="minechat.dvmn.org", env_var="CHAT_HOST", help='Host to connect to')
    p.add('--port', default=5000, type=int, env_var="CHAT_PORT", help='Port to listen')
    p.add('--history', default="./chat_log.txt", env_var="CHAT_HISTORY", help='Path to chat log')
    return p


async def delay_connection(connection_error_count: int, max_delay: int = 10):
    if connection_error_count >= 2:
        delay = min((connection_error_count - 1) * 2, max_delay)
        print(f"Пауза {delay} сек.")
        await asyncio.sleep(delay)


async def listen_to_chat(host, port, chat_log):
    connection_error_count = 0
    async with open(chat_log, "a") as chat_file:
        while True:
            try:
                reader, writer = await asyncio.open_connection(host, port)
                connection_error_count = 0
                while True:
                    data = await reader.readline()
                    msg = data.decode()
                    date_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
                    msg = f"[{date_str}] {msg}"
                    chat_file.write(msg)
                    print(msg)
            except ConnectionRefusedError:
                connection_error_count += 1
                print(f"Соединение отвергнуто.")
                await delay_connection(connection_error_count)
            except ConnectionResetError:
                connection_error_count += 1
                print(f"Соединение сброшено.")
                await delay_connection(connection_error_count, max_delay=15)


if __name__ == '__main__':
    arguments = create_argparser().parse_args()
    asyncio.run(listen_to_chat(arguments.host, arguments.port, arguments.history))
