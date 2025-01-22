from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.user import User
from app.db.db import get_db
from app.services.weather_service import WeatherService


router = Router()


class ProfileStates(StatesGroup):
    WEIGHT = State()
    HEIGHT = State()
    AGE = State()
    ACTIVITY = State()
    CITY = State()


@router.message(Command("start"))
async def start(message: Message):
    db = next(get_db())
    user = db.query(User).filter(User.user_id == message.from_user.id).first()

    builder = InlineKeyboardBuilder()
    if user:
        builder.button(text="⚙️ Настройки профиля", callback_data="profile_settings")
        builder.button(text="📊 Общий прогресс", callback_data="full_progress")
    else:
        builder.button(text="📝 Создать профиль", callback_data="create_profile")

    builder.adjust(1)
    await message.answer(
        "🏋️ Добро пожаловать в FitnessBot!\n\nВыберите действие снизу:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "create_profile")
async def create_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ваш вес в кг:")
    await state.set_state(ProfileStates.WEIGHT)


@router.message(ProfileStates.WEIGHT)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await message.answer("Введите ваш рост в см:")
    await state.set_state(ProfileStates.HEIGHT)


@router.message(ProfileStates.HEIGHT)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    await message.answer("Введите ваш возраст:")
    await state.set_state(ProfileStates.AGE)


@router.message(ProfileStates.AGE)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.answer("Сколько минут активности в день?")
    await state.set_state(ProfileStates.ACTIVITY)


@router.message(ProfileStates.ACTIVITY)
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=int(message.text))
    await message.answer("Введите ваш город:")
    await state.set_state(ProfileStates.CITY)


@router.message(ProfileStates.CITY)
async def process_city(message: Message, state: FSMContext):
    data = await state.get_data()
    weather = WeatherService().get_temperature(message.text)

    # Удаляем лишние ключи из data
    valid_fields = {"weight", "height", "age", "gender"}  # Поля, которые есть в модели User
    filtered_data = {k: v for k, v in data.items() if k in valid_fields}

    db = next(get_db())
    user = User(
        user_id=message.from_user.id,
        **filtered_data,  # Используем только допустимые поля
        city=message.text,
        water_level=calculate_water_goal(data, weather),
        calorie_level=calculate_calorie_goal(data)
    )
    db.add(user)
    db.commit()

    await message.answer(
        f"✅ Профиль создан!\n"
        f"🌡 Температура в городе {message.text}: {weather}°C\n"
        f"💧 Дневная норма воды: {user.water_level} мл\n"
        f"🔥 Дневная норма калорий: {user.calorie_level} ккал"
    )
    await state.clear()


def calculate_water_goal(data, temperature):
    base = data['weight'] * 30
    activity = (data['activity'] // 30) * 500
    temp_addition = 500 if temperature > 25 else 0
    return base + activity + temp_addition


def calculate_calorie_goal(data):
    return 10 * data['weight'] + 6.25 * data['height'] - 5 * data['age'] + 200