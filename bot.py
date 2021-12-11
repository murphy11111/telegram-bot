import config
from telebot import *
from main import bot, dp
from aiogram.types import Message
import sqlite3
from aiogram.types import *
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
import time
from multiprocessing import Process
import asyncio
from datetime import datetime

global_counter = 0
pars_text = "\n /watch_projects - просмотр существующих проектов. \n /time - тайм-менеджмент \n /watch_matireals_in_project - просмотр материалов в конкретном проекте "

# в серверной базе данных один раздел - projects и один стобец - name_of_project, во всех остальных раздел -

DB = sqlite3.connect("server.db")
sql_global = DB.cursor()  # работа с Бд
sql_global.execute(""" CREATE TABLE IF NOT EXISTS projects(name_of_project TEXT) """)
DB.commit()

events_bd = sqlite3.connect('time_management.db')
time_managment = events_bd.cursor()  # работа с Бд
time_managment.execute(""" CREATE TABLE IF NOT EXISTS info(id BIGINT, date TEXT, user_id INT, event TEXT) """)
events_bd.commit()


# объявляю класс для проекта в БД, чтобы использовать машину состояний
class Project(StatesGroup):
    name_project = State()
    new_matireals = State()
    parsing = State()


class Information(StatesGroup):
    name_of_project_for_all_function = State()
    name_of_project_for_parsing_function = State()
    parsing = State()


class repetitions(
    StatesGroup):  # этот класс нужен для отслеживания уже существующих проектов, чтобы не произошло повтореное создание проекта
    name_of_project_for_repetitions = State()


class add_project(StatesGroup):  # этот класс для добавления проекта на сервер
    added_project = State()
    addition_of_projects = State()  # этот атрибут нужен для того, чтобы понять нужно ли человеку добавить еще проект


# уведомление админу о запуске бота, также спец.функции для админа
async def send_to_admin(dp):
    await bot.send_message(chat_id=config.id_admin,
                           text="<b>D.o.p.i</b> запущен! Доступные функции :\n /add_projects - добавить проекты \n /add_materials - добавить материал \n /watch_projects - просмотр имеющихся проектов \n /watch_matireals_in_project - просмотр материалов в конкретном проекте  \n /time - функция напоминания ")


# приветственное сообщение обычному пользователю + функции для него
@dp.message_handler(commands="start")
async def HELLO(message: Message):
    await message.answer(
        text="<b>Привет! Я цифровой помощник по имени D.o.p.i. (Development of project ideas). Моя цель- помочь Вам создать проект.</b>")
    await message.answer(
        text="Смотрите что я умею: \n /watch_projects - просмотр существующих проектов. \n /time - функция напоминания \n /watch_matireals_in_project - просмотр материалов в конкретном проекте ")


# определяем сервер для БД, функция watch_cours
@dp.message_handler(commands=["watch_matireals_in_project"])
async def name_of_server(message: Message):
    inline_btn_1 = InlineKeyboardButton('Поиск по ключевым словам', callback_data='parsing')
    inline_btn_2 = InlineKeyboardButton('Смотреть все материалы', callback_data='all')
    inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1).add(inline_btn_2)
    await bot.send_message(message.from_user.id, text="выберите способ просмотра материалов", reply_markup=inline_kb1)


######parsingggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg
@dp.callback_query_handler(text='parsing')
async def watch_all_materials(message: Message):
    await Information.name_of_project_for_parsing_function.set()  # добавление в атрибут класса Information
    await bot.send_message(message.from_user.id,
                           text="<b>напишите название проекта</b> \n (если Вы хотите завершить просмотр материалов напишите 'stop')")


@dp.message_handler(state=Information.name_of_project_for_parsing_function)
async def Project_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name_of_project'] = message.text.lower()
    if data['name_of_project'] == 'stop':
        await bot.send_message(message.from_user.id, text='поиск завершен')
        await state.finish()
    else:
        sql_global.execute(f"SELECT name_of_project FROM projects where name_of_project = ?",
                           (data['name_of_project'],))
        if sql_global.fetchone() is None:
            try:
                buttom = ''

                for value in sql_global.execute("SELECT * FROM projects "):
                    word = str(value[0])

                    if any(word.find(str(x)) != -1 for x in str(message.text.lower()).split(' ')):
                        buttom = buttom + word + '\n'
                if buttom != '':
                    await bot.send_message(message.from_user.id, text='Возможно Вы имели ввиду:\n' + buttom)
                    await Information.name_of_project_for_parsing_function.set()  # добавление в атрибут класса Information
                    await bot.send_message(message.from_user.id,
                                           text="<b>напишите название проекта</b>(если нет проекта напишите 'stop')")
                else:
                    await bot.send_message(message.from_user.id,
                                           text='проекта такого нет. если хотите посмотреть, какие проекты существуют, то воспользуйтесь функцией /watch_projects ')
                    await state.finish()
            except Exception:
                await bot.send_message(message.from_user.id,
                                       text='произошла ошибка с подключением к базе данных или к другим серверам!')
                await state.finish()
        else:
            await Information.parsing.set()
            await bot.send_message(message.from_user.id, text="что хотите найти?")
            await bot.send_message(message.from_user.id, text="(если хотите завершить процесс поиска напишите 'stop')")


@dp.message_handler(state=Information.parsing)
async def Project_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['parsing'] = str(message.text).split(' ')
    if data['parsing'] == 'stop':
        await bot.send_message(message.from_user.id, text='функция завершена')
        await state.finish()
    else:
        Db = sqlite3.connect(str(data['name_of_project'] + '.db'))
        sql = Db.cursor()  # работа с Бд
        sql.execute(""" CREATE TABLE IF NOT EXISTS materials(material TEXT) """)
        Db.commit()
        for value in sql.execute("SELECT * FROM materials "):
            word = str(value[0])
            if any(word.find(str(x)) != -1 for x in data['parsing']):
                await bot.send_message(message.from_user.id, text=word)
    if message.from_user.id != config.id_admin:
        await bot.send_message(message.from_user.id,
                               text='просмотр завершен. Можете воспользоваться функциями \n /watch_projects - просмотр существующих проектов. \n /time - тайм-менеджмент \n /watch_matireals_in_project - просмотр материалов в конкретном проекте')
    else:
        await bot.send_message(message.from_user.id,
                               text='просмотр завершен. Можете воспользоваться функциями \n /watch_projects - просмотр существующих проектов. \n /time - тайм-менеджмент \n /watch_matireals_in_project - просмотр материалов в конкретном проекте \n /add_projects - добавить проект \n /add_materials - добавить материал')

    await state.finish()


#######allllllllllllllll
@dp.callback_query_handler(text='all')
async def watch_all_materials(message: Message):
    await Information.name_of_project_for_all_function.set()  # добавление в атрибут класса Information
    await bot.send_message(message.from_user.id,
                           text="<b>напишите название проекта</b> \n (если хотите прервать просмотр напишите 'stop')")


@dp.message_handler(state=Information.name_of_project_for_all_function)
async def Project_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name_of_project'] = message.text
    if data['name_of_project'] == 'stop':
        await bot.send_message(message.from_user.id, text='функция завершена')
        await state.finish()
    else:
        sql_global.execute(f"SELECT name_of_project FROM projects where name_of_project = ?",
                           (data['name_of_project'],))
        if sql_global.fetchone() is None:
            try:
                buttom = ''

                for value in sql_global.execute("SELECT * FROM projects "):
                    word = str(value[0]).lower()

                    if any(word.find(str(x)) != -1 for x in str(message.text.lower()).split(' ')):
                        buttom = buttom + word + '\n'
                if buttom != '':
                    await bot.send_message(message.from_user.id, text='Возможно Вы имели ввиду:\n' + buttom)
                    await Information.name_of_project_for_all_function.set()  # добавление в атрибут класса Information
                    await bot.send_message(message.from_user.id,
                                           text="</b>напишите название проекта</b>\n(если нет проекта напишите 'stop')")
                else:
                    await bot.send_message(message.from_user.id,
                                           text='проекта такого нет. если хотите посмотреть, какие проекты существуют, то воспользуйтесь функцией /watch_projects ')
                    await state.finish()
            except Exception:
                await bot.send_message(message.from_user.id,
                                       text='произошла ошибка с подключением к базе данных или к другим серверам!')
                await state.finish()
        else:
            Db = sqlite3.connect(str(data['name_of_project'] + '.db'))
            sql = Db.cursor()  # работа с Бд
            sql.execute(""" CREATE TABLE IF NOT EXISTS materials(material TEXT) """)
            Db.commit()
            for value in sql.execute("SELECT * FROM materials "):
                await bot.send_message(message.from_user.id, text=value[0])
            if message.from_user.id != config.id_admin:
                await bot.send_message(message.from_user.id,
                                       text='просмотр завершен. Можете воспользоваться функциями \n /watch_projects - просмотр существующих проектов. \n /time - тайм-менеджмент \n /watch_matireals_in_project - просмотр материалов в конкретном проекте')
            else:
                await bot.send_message(message.from_user.id,
                                       text='просмотр завершен. Можете воспользоваться функциями \n /watch_projects - просмотр существующих проектов. \n /time - тайм-менеджмент \n /watch_matireals_in_project - просмотр материалов в конкретном проекте \n /add_projects - добавить проект \n /add_materials - добавить материал')

            await state.finish()


####################################################################################### Доделать watch функцию !! класс Information


@dp.message_handler(commands=["add_projects"])
async def name_of_project_for_server(message: Message):
    if  message.from_user.id == config.id_admin:
        await add_project.added_project.set()  # добавление в атрибут класса add project
        await bot.send_message(chat_id=config.id_admin, text="<b>Напишите только ОДНО название проекта без символов</b>\nнапишите 'stop', чтобы прервать процесс")
    else:
        pass

@dp.message_handler(state=add_project.added_project)
async def search_for_repetitions(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['added_project'] = message.text
    sql_global.execute(f"SELECT name_of_project FROM projects where name_of_project = ?", (data['added_project'],))
    if data['added_project'] == 'stop':
        await message.answer(
            f'процесс остановлен! \n Функции: {pars_text}')
        await state.finish()
    else:
        if sql_global.fetchone() is None:
            try:
                sql_global.execute(f"INSERT INTO projects VALUES ('{data['added_project']}')")
                DB.commit()
                await bot.send_message(chat_id=config.id_admin, text='проект записан!')
            except Exception:
                await bot.send_message(chat_id=config.id_admin,
                                   text='произошла ошибка с подключением к sql или другим сервером!')
        else:
            await bot.send_message(chat_id=config.id_admin, text="такой проект уже есть!")

        await bot.send_message(chat_id=config.id_admin,
                           text="если хотите просмотреть проекты, которые уже существуют, вызовите команду /watch_project ")
        await add_project.addition_of_projects.set()  # добавление в атрибут класса add project
        await bot.send_message(chat_id=config.id_admin, text="хотите ли добавить еще один проект? (напишите да или нет)")


@dp.message_handler(state=add_project.addition_of_projects)
async def additions_of_projects(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['addition_of_projects'] = message.text.lower()
    if data['addition_of_projects'] == 'да':
        await add_project.added_project.set()  # добавление в атрибут класса add project
        await bot.send_message(chat_id=config.id_admin, text="<b>напишите только ОДНО название проекта без символов</b>")
    elif data['addition_of_projects'] == 'нет':
        await bot.send_message(chat_id=config.id_admin, text="как хотите.")
        await bot.send_message(chat_id=config.id_admin,
                               text="Доступные функции :\n /add_materials - добавить материал \n /watch_project - просмотр имеющихся проектов \n /watch_matireals_in_cours - просмотр материалов в конкретном проекте \n /add_projects - добавить проекты")
        await state.finish()
    else:
        await add_project.addition_of_projects.set()  # добавление в атрибут класса add project
        await bot.send_message(chat_id=config.id_admin,
                               text="Я Вас не понимаю. Хотите ли добавить еще один проект? (<b>напишите да или нет</b>)")


@dp.message_handler(commands='watch_projects')
async def watch_project(message: Message):
    for value in sql_global.execute("SELECT * FROM projects "):
        await bot.send_message(message.from_user.id, text=value[0])


###################################################################################################


# осуществление функцию add, определяем сервер для БД
@dp.message_handler(commands=["add_materials"])
async def name_of_server(message: Message):
    if message.from_user.id == config.id_admin:  # проверка на доступ
        await Project.name_project.set()  # добавление в атрибут класса Project
        await bot.send_message(chat_id=config.id_admin, text="<b>Напишите название проекта</b> \n (Напишите 'stop', чтобы прервать процесс)")


@dp.message_handler(state=Project.name_project)
async def open_project(message: Message, state: FSMContext):
    if message.from_user.id == config.id_admin:  # проверка на доступ
        async with state.proxy() as data:
            data['name_project'] = message.text
        if data['name_project'].lower() == 'stop':
            await message.answer(
                f'процесс остановлен! \n Функции: {pars_text}')
            await state.finish()
        else:
            sql_global.execute(f"SELECT name_of_project FROM projects where name_of_project = ?", (data['name_project'],))
            if sql_global.fetchone() is None:
                try:
                    await bot.send_message(chat_id=config.id_admin,
                                           text='Такого проекта нет. Если хотите посмотреть существующие проекты или добавить воспользуйтесь функциями : \n /watch_projects - просмотр имеющихся проектов \n /add_projects - добавить проекты  ')
                    await state.finish()
                except Exception:
                    await bot.send_message(chat_id=config.id_admin,
                                           text='произошла ошибка с подключением к sql или к другим серверам!')
            else:
                await Project.new_matireals.set()  # добавление в атрибут класса add project
                await bot.send_message(chat_id=config.id_admin,
                                       text="<b>добавьте материал (при написании комментария берите точное название(вопрос) с сайта, чтобы при парсинге не возникало проблем)</b> \n напишите 'stop', чтобы прервать процесс")


# добавление новых материалов
@dp.message_handler(state=Project.new_matireals)
async def finish(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['new_matireals'] = message.text
    if data['new_matireals']=='stop':
        await message.answer(
            f'процесс остановлен! \n Функции: {pars_text}')
        await state.finish()
    else:
        Db = sqlite3.connect(str(data['name_project'] + '.db'))
        sql = Db.cursor()  # работа с БД
        sql.execute(f""" CREATE TABLE IF NOT EXISTS materials(material TEXT) """)
        Db.commit()
        sql.execute(f"SELECT material FROM materials where material = ?", (data['new_matireals'],))

        if sql.fetchone() is None:
            try:
                sql.execute(f"INSERT INTO materials VALUES ('{data['new_matireals']}')")
                Db.commit()
                await bot.send_message(chat_id=config.id_admin, text='данные записаны успешно!')
                await state.finish()
            except Exception:
                await bot.send_message(chat_id=config.id_admin,
                                       text='произошла ошибка с подключением к sql или другим сервером!')
            finally:
                if Db:
                    Db.close()
        else:
            await bot.send_message(chat_id=config.id_admin, text="такие данные уже есть!")

        await bot.send_message(chat_id=config.id_admin,
                           text='/watch_matireals_in_project - просмотр материалов в данном проекте')

        await state.finish()


######## TIME
class time_menegment(StatesGroup):
    my_date = State()
    my_time = State()
    my_event = State()


@dp.message_handler(commands=['time'])
async def set_date(message: Message):
    await time_menegment.my_date.set()
    await message.answer(
        '<b>Эта функция нужна, чтобы помочь Вам не забыть о важном событии.</b>\nНапишите дату, когда Вам надо будет напомнить о событии.\n(<b>Формат:день.месяц.год</b>. например, 8.12.2021, где 8 - день, 12 - месяц, 2021 - год) \n напишите "stop" если хотите прервать процесс')


@dp.message_handler(state=time_menegment.my_date)
async def set_time(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = str(message.text.replace(' ', ''))
    list_date = list(data['date'].split('.'))
    if any(list_date[0] == str(x) for x in range(1, 10)):
        data['date'] = '0' + data['date']
    if any(list_date[1] == str(x) for x in range(1, 10)):
        list_date[1] = '0' + list_date[1]
        data['date'] = '.'.join(list_date)
    if data['date'].lower() == 'stop':
        await message.answer(
            f'процесс остановлен! \n Функции: {pars_text}')
        await state.finish()
    else:
        await time_menegment.my_time.set()
        await message.answer(
            'Напишите время, когда Вам надо будет напомнить о событии (<b>Формат : часы:минуты</b> например, 16:05 (0:30 - половина первого ночи )) \n напишите "stop" если хотите прервать процесс')


@dp.message_handler(state=time_menegment.my_time)
async def set_event(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = str(message.text.replace(' ', ''))
    list_time = list(data['time'].split(':'))
    if any(list_time[0] == str(x) for x in range(0, 10)):
        data['time'] = '0' + data['time']

    if data['time'].lower() == 'stop':
        await message.answer(
            f'процесс остановлен! \n Функции: {pars_text}')
        await state.finish()
    else:
        await time_menegment.my_event.set()
        await message.answer(
            'Напишите событие, которое Вам надо будет напомнить \n напишите "stop" если хотите прервать процесс')


@dp.message_handler(state=time_menegment.my_event)
async def set_event(message: Message, state: FSMContext):
    global global_counter
    async with state.proxy() as data:
        data['event'] = message.text

    if data['event'].lower() == 'stop':
        await message.answer(
            f'процесс остановлен! \n Функции: {pars_text}')
        await state.finish()
    else:
        try:
            date_and_time = data['date'] + '_' + data['time']
            users_id = int(message.from_user.id)
            try:
                for value in time_managment.execute("SELECT * FROM info "):
                    global_counter = value[0] + 1
            except:
                pass
            time_managment.execute(
                f"INSERT INTO info VALUES ('{global_counter}','{date_and_time}', '{users_id}','{'<b>НАПОМИНАНИЕ</b>: ' + data['event']}')")
            events_bd.commit()
            global_counter += 1
            await message.answer(f'Записано успешно!{pars_text}')
        except Exception:
            await message.answer(f'Произошла ошибка. Процесс остановлен.{pars_text}')
    await state.finish()


async def touch(wait_for):
    while True:
        i = 0
        for value in time_managment.execute("SELECT * FROM info "):
            if value[1] == datetime.now().strftime('%d.%m.%Y_%H:%M') or value[1] == datetime.now().strftime(
                    '%d.%m.%Y_%H.%M'):
                await bot.send_message(chat_id=value[2], text=value[3])
                time_managment.execute(f" DELETE FROM info WHERE id = {value[0]} ")
                events_bd.commit()
        await asyncio.sleep(wait_for)
