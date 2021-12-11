import config
import asyncio
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import *
from multiprocessing import Process

loop = asyncio.get_event_loop()


bot = Bot(token=config.API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

if __name__ == "__main__":
    from bot import dp, send_to_admin, touch

    loop.create_task(touch(10))

    executor.start_polling(dp, on_startup=send_to_admin, skip_updates= True)

