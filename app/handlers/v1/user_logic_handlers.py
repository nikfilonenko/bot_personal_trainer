from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io

from app.models.user import User, DailyData
from app.db.db import get_db
from app.services.weather_service import WeatherService


router = Router()


class ProfileStates(StatesGroup):
    WEIGHT = State()
    HEIGHT = State()
    AGE = State()
    ACTIVITY = State()
    CITY = State()


class EditProfileStates(StatesGroup):
    WEIGHT = State()
    HEIGHT = State()
    AGE = State()
    ACTIVITY = State()
    CITY = State()


def get_main_menu_keyboard(user_exists: bool) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    if user_exists:
        builder.button(text="Do it 🏆 or 🍎", callback_data="worker")
        builder.button(text="📊 Статистика", callback_data="statistics")
        builder.button(text="⚙️ Настройки профиля", callback_data="profile_settings")
        builder.button(text="✨ Что умеет бот?", callback_data="bot_can_do")
    else:
        builder.button(text="📝 Создать профиль", callback_data="set_profile")
        builder.button(text="❓ Подробнее о боте", callback_data="about_bot")

    builder.adjust(2)
    return builder


async def show_main_menu(callback_or_message: CallbackQuery | Message):
    with get_db() as db:
        user_id = (
            callback_or_message.from_user.id
            if isinstance(callback_or_message, CallbackQuery)
            else callback_or_message.from_user.id
        )
        user = db.query(User).filter(User.user_id == user_id).first()
        user_exists = user is not None

        builder = get_main_menu_keyboard(user_exists)
        text = "🏋️ Добро пожаловать в FitnessBot!\n\nВыберите действие снизу:"

        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(text, reply_markup=builder.as_markup())
        else:
            await callback_or_message.answer(text, reply_markup=builder.as_markup())


async def show_menu_with_back_button(
    callback: CallbackQuery,
    text: str,
    back_callback_data: str = "start"
):
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data=back_callback_data)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.message(Command("start"))
async def start(message: Message):
    await show_main_menu(message)


@router.callback_query(F.data == "set_profile")
async def set_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ваш вес в кг:")
    await state.set_state(ProfileStates.WEIGHT)


@router.message(ProfileStates.WEIGHT)
async def process_weight(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")

    await state.update_data(weight=float(message.text))
    await message.answer("Введите ваш рост в см:")
    await state.set_state(ProfileStates.HEIGHT)


@router.message(ProfileStates.HEIGHT)
async def process_height(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")

    await state.update_data(height=float(message.text))
    await message.answer("Введите ваш возраст:")
    await state.set_state(ProfileStates.AGE)


@router.message(ProfileStates.AGE)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")

    await state.update_data(age=int(message.text))
    await message.answer("Сколько минут активности в день?")
    await state.set_state(ProfileStates.ACTIVITY)


@router.message(ProfileStates.ACTIVITY)
async def process_activity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")

    await state.update_data(activity=int(message.text))
    await message.answer("Введите ваш город:")
    await state.set_state(ProfileStates.CITY)


@router.message(ProfileStates.CITY)
async def process_city(message: Message, state: FSMContext):
    data = await state.get_data()
    weather = WeatherService().get_temperature(message.text)

    valid_fields = {"weight", "height", "age", "gender"}
    filtered_data = {k: v for k, v in data.items() if k in valid_fields}

    with get_db() as db:
        user = User(
            user_id=message.from_user.id,
            **filtered_data,
            city=message.text,
            water_level=calculate_water_goal(data, weather),
            calorie_level=calculate_calorie_goal(data)
        )
        db.add(user)
        db.commit()

        await message.answer(
            f"✅ Профиль создан!\n\n"
            f"🌡 Температура в городе {message.text}: {weather}°C\n"
            f"💧 Дневная норма воды: {user.water_level} мл\n"
            f"🔥 Дневная норма калорий: {user.calorie_level} ккал",
            reply_markup=InlineKeyboardBuilder()
            .button(text="👍 Перейти к тренировкам/отслеживанию калорий", callback_data="start")
            .as_markup()
        )
        await state.clear()


@router.callback_query(F.data == "profile_settings")
async def profile_settings(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить вес", callback_data="edit_weight")
    builder.button(text="✏️ Изменить рост", callback_data="edit_height")
    builder.button(text="✏️ Изменить возраст", callback_data="edit_age")
    builder.button(text="✏️ Изменить активность", callback_data="edit_activity")
    builder.button(text="✏️ Изменить город", callback_data="edit_city")
    builder.button(text="◀️ Назад", callback_data="start")
    builder.adjust(2, 2, 1)

    await callback.message.edit_text(
        "⚙️ Настройки профиля:\n\nВыберите параметр для изменения:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "edit_weight")
async def edit_weight(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новый вес в кг:")
    await state.set_state(EditProfileStates.WEIGHT)


@router.message(EditProfileStates.WEIGHT)
async def process_edit_weight(message: Message, state: FSMContext):
    data = await state.get_data()

    if not message.text.isdigit():
        return await message.answer("Введите число!")

    with get_db() as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if not user:
            return await message.answer("❌ Профиль не найден. Сначала создайте профиль.")

        weather = WeatherService().get_temperature(user.city)

        user.weight = float(message.text)
        user.water_level = calculate_water_goal({
            "weight": user.weight,
            "activity": data.get("activity", 0)
        }, weather)
        user.calorie_level = calculate_calorie_goal({
            "weight": user.weight,
            "height": user.height,
            "age": user.age
        })
        db.commit()

        updated_text = (
            f"✅ Вес успешно изменён!\n\n"
            f"🌡 Температура в городе {user.city}: {weather}°C\n"
            f"💧 Дневная норма воды: {user.water_level} мл\n"
            f"🔥 Дневная норма калорий: {user.calorie_level} ккал"
        )

        await message.answer(updated_text)

    await state.clear()
    await show_main_menu(message)


@router.callback_query(F.data == "edit_height")
async def edit_height(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новый рост в см:")
    await state.set_state(EditProfileStates.HEIGHT)


@router.message(EditProfileStates.HEIGHT)
async def process_edit_height(message: Message, state: FSMContext):
    data = await state.get_data()

    if not message.text.isdigit():
        return await message.answer("Введите число!")

    with get_db() as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if not user:
            return await message.answer("❌ Профиль не найден. Сначала создайте профиль.")

        weather = WeatherService().get_temperature(user.city)

        user.height = float(message.text)
        user.water_level = calculate_water_goal({
            "weight": user.weight,
            "activity": data.get("activity", 0)
        }, weather)
        user.calorie_level = calculate_calorie_goal({
            "weight": user.weight,
            "height": user.height,
            "age": user.age
        })
        db.commit()

        updated_text = (
            f"✅ Рост успешно изменён!\n\n"
            f"🌡 Температура в городе {user.city}: {weather}°C\n"
            f"💧 Дневная норма воды: {user.water_level} мл\n"
            f"🔥 Дневная норма калорий: {user.calorie_level} ккал"
        )

        await message.answer(updated_text)

    await state.clear()
    await show_main_menu(message)


@router.callback_query(F.data == "edit_age")
async def edit_age(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новый возраст:")
    await state.set_state(EditProfileStates.AGE)


@router.message(EditProfileStates.AGE)
async def process_edit_age(message: Message, state: FSMContext):
    data = await state.get_data()

    if not message.text.isdigit():
        return await message.answer("Введите число!")

    with get_db() as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if not user:
            return await message.answer("❌ Профиль не найден. Сначала создайте профиль.")

        weather = WeatherService().get_temperature(user.city)

        user.age = int(message.text)
        user.water_level = calculate_water_goal({
            "weight": user.weight,
            "activity": data.get("activity", 0)
        }, weather)
        user.calorie_level = calculate_calorie_goal({
            "weight": user.weight,
            "height": user.height,
            "age": user.age
        })
        db.commit()

        updated_text = (
            f"✅ Возраст успешно изменён!\n\n"
            f"🌡 Температура в городе {user.city}: {weather}°C\n"
            f"💧 Дневная норма воды: {user.water_level} мл\n"
            f"🔥 Дневная норма калорий: {user.calorie_level} ккал"
        )

        await message.answer(updated_text)

    await state.clear()
    await show_main_menu(message)


@router.callback_query(F.data == "edit_activity")
async def edit_activity(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новое количество минут активности в день:")
    await state.set_state(EditProfileStates.ACTIVITY)


@router.message(EditProfileStates.ACTIVITY)
async def process_edit_activity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")

    with get_db() as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if not user:
            return await message.answer("❌ Профиль не найден. Сначала создайте профиль.")

        weather = WeatherService().get_temperature(user.city)

        activity = int(message.text)
        user.water_level = calculate_water_goal({
            "weight": user.weight,
            "activity": activity
        }, weather)
        user.calorie_level = calculate_calorie_goal({
            "weight": user.weight,
            "height": user.height,
            "age": user.age
        })
        db.commit()

        updated_text = (
            f"✅ Активность успешно изменена!\n\n"
            f"🌡 Температура в городе {user.city}: {weather}°C\n"
            f"💧 Дневная норма воды: {user.water_level} мл\n"
            f"🔥 Дневная норма калорий: {user.calorie_level} ккал"
        )

        await message.answer(updated_text)

    await state.clear()
    await show_main_menu(message)


@router.callback_query(F.data == "edit_city")
async def edit_city(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новый город:")
    await state.set_state(EditProfileStates.CITY)


@router.message(EditProfileStates.CITY)
async def process_edit_city(message: Message, state: FSMContext):
    data = await state.get_data()

    if not message.text.strip():
        return await message.answer("Введите название города!")

    with get_db() as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if not user:
            return await message.answer("❌ Профиль не найден. Сначала создайте профиль.")

        weather = WeatherService().get_temperature(message.text)

        user.city = message.text
        user.water_level = calculate_water_goal({
            "weight": user.weight,
            "activity": data.get("activity", 0)
        }, weather)
        user.calorie_level = calculate_calorie_goal({
            "weight": user.weight,
            "height": user.height,
            "age": user.age
        })
        db.commit()

        updated_text = (
            f"✅ Город успешно изменён!\n\n"
            f"🌡 Температура в городе {user.city}: {weather}°C\n"
            f"💧 Дневная норма воды: {user.water_level} мл\n"
            f"🔥 Дневная норма калорий: {user.calorie_level} ккал"
        )

        await message.answer(updated_text)

    await state.clear()
    await show_main_menu(message)


@router.callback_query(F.data == "statistics")
async def statistics(callback: CallbackQuery):
    await callback.message.delete()

    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Статистика за день", callback_data="daily_statistics")
    builder.button(text="📈 График за день", callback_data="daily_progress_graph")
    builder.button(text="📊 График за месяц", callback_data="monthly_progress_graph")
    builder.button(text="🏆 Ачивки", callback_data="achievements")
    builder.button(text="◀️ Назад", callback_data="start")
    builder.adjust(2, 2, 1)

    await callback.message.answer(
        "Выберите тип статистики:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "daily_statistics")
async def daily_statistics(callback: CallbackQuery):
    with get_db() as db:
        user = db.query(User).filter(User.user_id == callback.from_user.id).first()
        if user:
            daily_data = db.query(DailyData).filter(DailyData.user_id == user.user_id, DailyData.date == datetime.today().date()).first()
            if daily_data:
                text = (
                    f"📅 Статистика за день:\n\n"
                    f"💧 Выпито воды: {daily_data.logged_water} мл из {user.water_level} мл\n"
                    f"🍎 Потреблено калорий: {daily_data.logged_calories} ккал из {user.calorie_level} ккал\n"
                    f"🔥 Сожжено калорий: {daily_data.burned_calories} ккал"
                )
            else:
                text = "📅 Статистика за день:\n\nДанные за сегодня отсутствуют."
        else:
            text = "❌ Профиль не найден. Сначала создайте профиль."

    await show_menu_with_back_button(callback, text)


@router.callback_query(F.data == "daily_progress_graph")
async def daily_progress_graph(callback: CallbackQuery):
    with get_db() as db:
        user = db.query(User).filter(User.user_id == callback.from_user.id).first()
        if user:
            daily_data = db.query(DailyData).filter(DailyData.user_id == user.user_id, DailyData.date == datetime.today().date()).first()
            if daily_data:
                await callback.message.delete()

                labels = ["Вода", "Калории", "Сожжено"]
                values = [daily_data.logged_water, daily_data.logged_calories, daily_data.burned_calories]
                goals = [user.water_level, user.calorie_level, 0]

                fig, ax = plt.subplots()
                ax.bar(labels, values, label="Факт")
                ax.bar(labels, goals, alpha=0.5, label="Цель")
                ax.set_ylabel("Значение")
                ax.set_title("Прогресс за день")
                ax.legend()

                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()

                photo = BufferedInputFile(buf.getvalue(), filename="progress.png")

                builder = InlineKeyboardBuilder()
                builder.button(text="◀️ Назад", callback_data="statistics")
                await callback.message.answer_photo(
                    photo,
                    caption="📈 График прогресса за день:",
                    reply_markup=builder.as_markup()
                )
            else:
                await callback.message.answer("📅 Данные за сегодня отсутствуют.")
                builder = InlineKeyboardBuilder()
                builder.button(text="◀️ Назад", callback_data="statistics")
                await callback.answer(
                    reply_markup=builder.as_markup()
                )
        else:
            await callback.message.answer("❌ Профиль не найден. Сначала создайте профиль.")


@router.callback_query(F.data == "monthly_progress_graph")
async def monthly_progress_graph(callback: CallbackQuery):
    with get_db() as db:
        user = db.query(User).filter(User.user_id == callback.from_user.id).first()
        if user:
            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=30)
            daily_data = db.query(DailyData).filter(DailyData.user_id == user.user_id, DailyData.date >= start_date, DailyData.date <= end_date).all()

            if daily_data:
                await callback.message.delete()

                dates = [data.date for data in daily_data]
                water = [data.logged_water for data in daily_data]
                calories = [data.logged_calories for data in daily_data]
                burned = [data.burned_calories for data in daily_data]

                fig, ax = plt.subplots()
                ax.plot(dates, water, label="Вода")
                ax.plot(dates, calories, label="Калории")
                ax.plot(dates, burned, label="Сожжено")
                ax.set_ylabel("Значение")
                ax.set_title("Прогресс за месяц")
                ax.legend()

                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()

                photo = BufferedInputFile(buf.getvalue(), filename="monthly_progress.png")

                builder = InlineKeyboardBuilder()
                builder.button(text="◀️ Назад", callback_data="statistics")
                await callback.message.answer_photo(
                    photo,
                    caption="📊 График прогресса за месяц:",
                    reply_markup=builder.as_markup()
                )
            else:
                await callback.message.answer("📅 Данные за последний месяц отсутствуют.")
        else:
            await callback.message.answer("❌ Профиль не найден. Сначала создайте профиль.")


@router.callback_query(F.data == "achievements")
async def achievements(callback: CallbackQuery):
    with get_db() as db:
        user = db.query(User).filter(User.user_id == callback.from_user.id).first()
        if user:
            achievements = [
                "🏅 Выпито 2 литра воды за день",
                "🏅 Сожжено 500 ккал за тренировку",
                "🏅 Достигнута дневная норма калорий",
            ]
            text = "🏆 Ваши ачивки:\n\n" + "\n".join(achievements)
        else:
            text = "❌ Профиль не найден. Сначала создайте профиль."

    await show_menu_with_back_button(callback, text)


@router.callback_query(F.data == "bot_can_do")
async def bot_can_do(callback: CallbackQuery):
    await show_menu_with_back_button(
        callback,
        "✨ Что умеет бот:\n\n"
        "1. Рассчитывать дневные нормы воды и калорий.\n"
        "2. Логировать воду, еду и тренировки.\n"
        "3. Отслеживать прогресс.\n"
        "4. Учитывать погоду для расчёта нормы воды."
    )


@router.callback_query(F.data == "about_bot")
async def about_bot(callback: CallbackQuery):
    await show_menu_with_back_button(
        callback,
        "❓ Подробнее о боте:\n\n"
        "Этот бот помогает Вам следить за здоровьем, рассчитывая нормы воды и калорий, "
        "а также отслеживая вашу активность и питание."
    )


@router.callback_query(F.data == "worker")
async def worker(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.button(text="💧 Вода", callback_data="log_water")
    builder.button(text="🍎 Еда", callback_data="log_food")
    builder.button(text="🏋️ Тренировка", callback_data="log_workout")
    builder.button(text="📊 Прогресс", callback_data="progress")
    builder.button(text="◀️ В главное меню", callback_data="start")

    builder.adjust(2, 2, 1)

    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "start")
async def back_to_start(callback: CallbackQuery):
    await show_main_menu(callback)


def calculate_water_goal(data, temperature):
    base = data['weight'] * 30
    activity = (data['activity'] // 30) * 500
    temp_addition = 500 if temperature > 25 else 0
    return base + activity + temp_addition


def calculate_calorie_goal(data):
    return (10 * data['weight'] + 6.25 * data['height'] - 5 * data['age']) * 1.5