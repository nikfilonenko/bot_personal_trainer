from datetime import date

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.models.user import User, DailyData
from app.db.db import get_db
from app.services.nutrition_cal_service import NutritionService
from app.services.workout_service import WorkoutService


router = Router()


class ActivitiesStates(StatesGroup):
    LOG_FOOD = State()  # Состояние для логирования еды


def get_daily_data(user_id: int):
    db = next(get_db())
    user = db.query(User).filter(User.user_id == user_id).first()
    daily = db.query(DailyData).filter(
        DailyData.user_id == user.user_id,
        DailyData.date == date.today()
    ).first()

    if not daily:
        daily = DailyData(
            user_id=user.user_id,
            date=date.today(),
            logged_water=0,
            logged_calories=0,
            burned_calories=0
        )
        db.add(daily)
        db.commit()
    return daily


@router.message(Command("log_water"))
async def log_water(message: Message):
    db = next(get_db())
    user = db.query(User).filter(User.user_id == message.from_user.id).first()

    if not user:
        return await message.answer("Сначала создайте профиль!")

    try:
        amount = float(message.text.split()[1])
        daily = get_daily_data(message.from_user.id)
        daily.logged_water += amount
        db.commit()

        remaining = user.water_level - daily.logged_water
        await message.answer(f"💧 Записано {amount} мл воды. Осталось: {remaining} мл")
    except:
        await message.answer("Используйте: /log_water <количество>")


@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    try:
        query = " ".join(message.text.split()[1:])
        nutrition_service = NutritionService()
        nutrition_info = nutrition_service.get_nutrition_info(query)

        if nutrition_info:
            # Сохраняем информацию о продукте в состоянии
            await state.update_data(nutrition_info=nutrition_info[0])
            await message.answer(
                f"🍎 {nutrition_info[0]['name']} - {nutrition_info[0]['calories']} ккал/100г\n"
                "Сколько грамм вы съели?"
            )
            # Переводим пользователя в состояние LOG_FOOD
            await state.set_state(ActivitiesStates.LOG_FOOD)
        else:
            await message.answer("Не удалось найти информацию о продукте.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(ActivitiesStates.LOG_FOOD, F.text.regexp(r"^\d+$"))
async def process_food_amount(message: Message, state: FSMContext):
    db = next(get_db())
    user = db.query(User).filter(User.user_id == message.from_user.id).first()

    if not user:
        await message.answer("Сначала создайте профиль!")
        return

    # Получаем данные о продукте из состояния
    data = await state.get_data()
    nutrition_info = data.get("nutrition_info")

    if not nutrition_info:
        await message.answer("Ошибка: информация о продукте не найдена.")
        return

    try:
        grams = int(message.text)
        calories = grams * 0.01 * nutrition_info['calories']

        # Получаем или создаём запись за сегодня
        daily = get_daily_data(message.from_user.id)
        daily.logged_calories += calories
        db.commit()

        await message.answer(f"🍽 Записано {grams}г. Добавлено {calories:.1f} ккал")
        await state.clear()  # Завершаем состояние
    except ValueError:
        await message.answer("Пожалуйста, введите число.")


@router.message(Command("log_workout"))
async def log_workout(message: Message):
    try:
        activity = " ".join(message.text.split()[1:-1])
        duration = int(message.text.split()[-1])
        workout = WorkoutService().get_calories_burned(activity, duration)

        if workout:
            daily = get_daily_data(message.from_user.id)
            daily.burned_calories += workout[0]['total_calories']
            await message.answer(
                f"🏃♂️ {workout[0]['activity']} {duration} мин - {workout[0]['total_calories']} ккал"
            )
    except:
        await message.answer("Используйте: /log_workout <активность> <минуты>")


@router.message(Command("progress"))
async def show_progress(message: Message):
    db = next(get_db())
    user = db.query(User).filter(User.user_id == message.from_user.id).first()
    daily = get_daily_data(message.from_user.id)

    progress = (
        f"📅 Прогресс за {daily.date}:\n"
        f"💧 Вода: {daily.logged_water}/{user.water_level} мл\n"
        f"🍎 Калории: {daily.logged_calories:.1f}/{user.calorie_level} ккал\n"
        f"🔥 Сожжено: {daily.burned_calories} ккал"
    )
    await message.answer(progress)