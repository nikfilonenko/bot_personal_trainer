from datetime import date

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session

from app.models.user import User, DailyData
from app.db.db import get_db
from app.services.nutrition_cal_service import NutritionService
from app.services.workout_service import WorkoutService


router = Router()


class ActivitiesStates(StatesGroup):
    LOG_WATER = State()
    LOG_FOOD = State()
    LOG_FOOD_AMOUNT = State()
    LOG_WORKOUT_TYPE = State()
    LOG_WORKOUT_DURATION = State()


def get_daily_data(user_id: int, db: Session):
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


@router.callback_query(F.data == "log_water")
async def log_water(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("💧 Введите количество воды в мл:")
    await state.set_state(ActivitiesStates.LOG_WATER)


@router.message(ActivitiesStates.LOG_WATER, F.text.regexp(r"^\d+$"))
async def process_water(message: Message, state: FSMContext):
    with get_db() as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if not user:
            return await message.answer("Сначала создайте профиль!")

        try:
            amount = float(message.text)
            daily = get_daily_data(message.from_user.id, db)
            daily.logged_water += amount
            db.commit()

            remaining = user.water_level - daily.logged_water
            await message.answer(
                f"💧 Записано {amount} мл воды. Осталось: {remaining} мл",
                reply_markup=InlineKeyboardBuilder()
                .button(text="◀️ Назад", callback_data="worker")
                .as_markup()
            )
        except:
            await message.answer(
                "Ошибка. Введите число.",
                reply_markup=InlineKeyboardBuilder()
                .button(text="◀️ Назад", callback_data="worker")
                .as_markup()
            )
    await state.clear()


@router.callback_query(F.data == "log_food")
async def log_food(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🍎 Введите название продукта:",
        reply_markup=InlineKeyboardBuilder()
        .button(text="◀️ Назад", callback_data="worker")
        .as_markup()
    )
    await state.set_state(ActivitiesStates.LOG_FOOD)


@router.message(ActivitiesStates.LOG_FOOD)
async def process_food(message: Message, state: FSMContext):
    try:
        query = message.text
        nutrition_service = NutritionService()
        nutrition_info = await nutrition_service.get_nutrition_info(query)

        if nutrition_info:
            await state.update_data(nutrition_info=nutrition_info)
            await message.answer(
                f"🍎 {nutrition_info['name']} - {nutrition_info['calories']} ккал/100г\n"
                "Сколько грамм вы съели?",
                reply_markup=InlineKeyboardBuilder()
                .button(text="◀️ Назад", callback_data="worker")
                .as_markup()
            )
            await state.set_state(ActivitiesStates.LOG_FOOD_AMOUNT)
        else:
            await message.answer(
                "Продукт не найден. Попробуйте еще раз.",
                reply_markup=InlineKeyboardBuilder()
                .button(text="◀️ Назад", callback_data="worker")
                .as_markup()
            )
    except Exception as e:
        await message.answer(
            f"Ошибка: {e}",
            reply_markup=InlineKeyboardBuilder()
            .button(text="◀️ Назад", callback_data="worker")
            .as_markup()
        )


@router.message(ActivitiesStates.LOG_FOOD_AMOUNT, F.text.regexp(r"^\d+$"))
async def process_food_amount(message: Message, state: FSMContext):
    with get_db() as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if not user:
            return await message.answer("Сначала создайте профиль!")

        data = await state.get_data()
        nutrition_info = data.get("nutrition_info")

        if not nutrition_info:
            return await message.answer(
                "Ошибка: информация о продукте не найдена.",
                reply_markup=InlineKeyboardBuilder()
                .button(text="◀️ Назад", callback_data="worker")
                .as_markup()
            )

        try:
            grams = int(message.text)
            calories = grams * 0.01 * nutrition_info['calories']

            daily = get_daily_data(message.from_user.id, db)
            daily.logged_calories += calories
            db.commit()

            await message.answer(
                f"🍽 Записано {grams}г. Добавлено {calories:.1f} ккал",
                reply_markup=InlineKeyboardBuilder()
                .button(text="◀️ Назад", callback_data="worker")
                .as_markup()
            )
        except ValueError:
            await message.answer(
                "Пожалуйста, введите число.",
                reply_markup=InlineKeyboardBuilder()
                .button(text="◀️ Назад", callback_data="worker")
                .as_markup()
            )
    await state.clear()


def calculate_water_for_workout(duration_minutes: int) -> int:
    return (duration_minutes // 60) * 500


@router.callback_query(F.data == "log_workout")
async def log_workout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏋️ Введите тип тренировки (например, 'бег'):",
        reply_markup=InlineKeyboardBuilder()
        .button(text="◀️ Назад", callback_data="worker")
        .as_markup()
    )
    await state.set_state(ActivitiesStates.LOG_WORKOUT_TYPE)


@router.message(ActivitiesStates.LOG_WORKOUT_TYPE)
async def process_workout_type(message: Message, state: FSMContext):
    activity = message.text
    await state.update_data(activity=activity)

    await message.answer(
        "⏱ Введите продолжительность тренировки в минутах (например, '30'):",
        reply_markup=InlineKeyboardBuilder()
        .button(text="◀️ Назад", callback_data="worker")
        .as_markup()
    )
    await state.set_state(ActivitiesStates.LOG_WORKOUT_DURATION)


@router.message(ActivitiesStates.LOG_WORKOUT_DURATION, F.text.regexp(r"^\d+$"))
async def process_workout_duration(message: Message, state: FSMContext):
    duration = int(message.text)
    data = await state.get_data()
    activity = data.get("activity")

    workout_service = WorkoutService()
    calories_burned = workout_service.get_calories_burned(activity, duration)

    if not calories_burned:
        return await message.answer(
            "Тренировка не найдена. Попробуйте еще раз.",
            reply_markup=InlineKeyboardBuilder()
            .button(text="◀️ Назад", callback_data="worker")
            .as_markup()
        )

    with get_db() as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if not user:
            return await message.answer("Сначала создайте профиль!")

        daily = get_daily_data(message.from_user.id, db)
        daily.burned_calories += calories_burned[0]['total_calories']
        db.commit()

        water_to_drink = calculate_water_for_workout(duration)

        response_text = (
            f"🏋️ Тренировка: {activity}\n"
            f"⏱ Продолжительность: {duration} мин\n"
            f"🔥 Сожжено калорий: {calories_burned[0]['total_calories']:.1f}\n"
            f"💧 Рекомендуется выпить воды: {water_to_drink} мл"
        )

        await message.answer(
            response_text,
            reply_markup=InlineKeyboardBuilder()
            .button(text="◀️ Назад", callback_data="worker")
            .as_markup()
        )
    await state.clear()


@router.callback_query(F.data == "progress")
async def show_progress(callback: CallbackQuery):
    with get_db() as db:
        user = db.query(User).filter(User.user_id == callback.from_user.id).first()

        if not user:
            return await callback.message.answer(
                "Сначала создайте профиль!",
                reply_markup=InlineKeyboardBuilder()
                .button(text="◀️ Назад", callback_data="worker")
                .as_markup()
            )

        daily = get_daily_data(callback.from_user.id, db)

        water_status = "✅ Норма выполнена" if daily.logged_water >= user.water_level else "❌ Норма не выполнена"
        calories_status = "✅ Норма выполнена" if daily.logged_calories >= user.calorie_level else "❌ Норма не выполнена"
        burned_status = "✅ Норма выполнена" if daily.burned_calories >= user.calorie_level else "❌ Норма не выполнена"

        progress_text = (
            f"📅 Прогресс за {daily.date}:\n\n"
            f"💧 Вода: {daily.logged_water}/{user.water_level} мл {water_status}\n"
            f"🍎 Калории: {daily.logged_calories:.1f}/{user.calorie_level} ккал {calories_status}\n"
            f"🔥 Сожжено: {daily.burned_calories} ккал {burned_status}"
        )

        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад", callback_data="worker")

        await callback.message.edit_text(
            progress_text,
            reply_markup=builder.as_markup()
        )