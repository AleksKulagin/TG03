import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import logging
import sqlite3

from config import TOKEN

API_TOKEN = TOKEN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Создаем подключение к базе данных school_data.db
def db_setup():
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            grade TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn

conn = db_setup()

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Определение состояний
class FormStates(StatesGroup):
    name = State()
    age = State()
    grade = State()

# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Я бот для сбора данных. Введите ваше имя:")
    await state.set_state(FormStates.name)

# Хэндлер для получения имени
@router.message(FormStates.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш возраст:")
    await state.set_state(FormStates.age)

# Хэндлер для получения возраста
@router.message(FormStates.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Введите ваш класс:")
    await state.set_state(FormStates.grade)

# Хэндлер для получения класса и сохранения данных
@router.message(FormStates.grade)
async def process_grade(message: Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data['name']
    age = user_data['age']
    grade = message.text

    cursor = conn.cursor()
    cursor.execute('INSERT INTO students (name, age, grade) VALUES (?, ?, ?)', (name, age, grade))
    conn.commit()

    await message.answer("Данные сохранены! Для просмотра всех записей введите /list.")
    await state.clear()

# Хэндлер на команду /list для отображения всех записей
@router.message(Command("list"))
async def cmd_list(message: Message):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students')
    records = cursor.fetchall()
    if records:
        response = "\n".join([f"ID: {record[0]}, Name: {record[1]}, Age: {record[2]}, Grade: {record[3]}" for record in records])
    else:
        response = "Нет записей."
    await message.answer(response)

# Хэндлер на команду /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "/start - начать диалог с ботом\n"
        "/list - показать все записи\n"
        "/help - показать эту справку"
    )
    await message.answer(help_text)

# Добавление роутера в диспетчер
dp.include_router(router)

# Функция запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())