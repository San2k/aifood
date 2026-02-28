"""
Settings command handler for user goals configuration.
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..keyboards.inline import get_settings_keyboard, get_goal_selection_keyboard
from ...services.agent_client import AgentClient
from ...config import settings as app_settings

logger = logging.getLogger(__name__)

router = Router()

# Initialize agent client
agent_client = AgentClient(app_settings.AGENT_API_URL)


class SettingsStates(StatesGroup):
    """FSM states for settings configuration."""
    waiting_for_calories = State()
    waiting_for_protein = State()
    waiting_for_carbs = State()
    waiting_for_fat = State()
    waiting_for_goal_selection = State()
    # Physical parameters states
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_height = State()
    waiting_for_weight = State()
    waiting_for_activity = State()


@router.message(Command("settings"))
async def cmd_settings(message: Message, state: FSMContext):
    """
    Handle /settings command.
    Shows current goals and options to configure.
    """
    try:
        telegram_id = message.from_user.id

        # Get user profile from agent-api
        profile = await agent_client.get_user_profile(telegram_id)

        if not profile:
            await message.answer(
                "❌ Не удалось загрузить ваш профиль.\n"
                "Используйте /start для регистрации."
            )
            return

        # Format current goals
        current_goals = _format_goals(profile)

        await message.answer(
            f"⚙️ **Ваши текущие настройки**\n\n"
            f"{current_goals}\n\n"
            f"Что хотите настроить?",
            reply_markup=get_settings_keyboard(),
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error in settings command: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(F.data == "settings_physical")
async def settings_configure_physical(callback: CallbackQuery, state: FSMContext):
    """Handle physical parameters configuration."""
    await callback.answer()

    await callback.message.edit_text(
        "👤 **Настройка физических параметров**\n\n"
        "Введите ваш **возраст** (например: 25):",
        parse_mode="Markdown"
    )
    await state.set_state(SettingsStates.waiting_for_age)


@router.message(SettingsStates.waiting_for_age)
async def settings_age_received(callback: Message, state: FSMContext):
    """Handle age input."""
    try:
        age = int(callback.text.strip())

        if age < 10 or age > 120:
            await callback.answer("⚠️ Пожалуйста, введите реальный возраст (10-120):")
            return

        await state.update_data(age=age)

        await callback.answer(
            f"✅ Возраст: {age} лет\n\n"
            f"Теперь укажите ваш **пол**:\n\n"
            f"Введите: male (мужской) или female (женский)"
        )
        await state.set_state(SettingsStates.waiting_for_gender)

    except ValueError:
        await callback.answer("⚠️ Пожалуйста, введите число:")


@router.message(SettingsStates.waiting_for_gender)
async def settings_gender_received(callback: Message, state: FSMContext):
    """Handle gender input."""
    gender_input = callback.text.strip().lower()

    gender_map = {
        "male": "male",
        "м": "male",
        "мужской": "male",
        "м": "male",
        "female": "female",
        "ж": "female",
        "женский": "female",
        "ж": "female"
    }

    gender = gender_map.get(gender_input)

    if not gender:
        await callback.answer(
            "⚠️ Пожалуйста, введите male (мужской) или female (женский):"
        )
        return

    await state.update_data(gender=gender)

    gender_display = "Мужской" if gender == "male" else "Женский"
    await callback.answer(
        f"✅ Пол: {gender_display}\n\n"
        f"Теперь введите ваш **рост в сантиметрах** (например: 175):"
    )
    await state.set_state(SettingsStates.waiting_for_height)


@router.message(SettingsStates.waiting_for_height)
async def settings_height_received(callback: Message, state: FSMContext):
    """Handle height input."""
    try:
        height_text = callback.text.strip().replace(",", ".")
        height_cm = float(height_text)

        if height_cm < 100 or height_cm > 250:
            await callback.answer("⚠️ Пожалуйста, введите реальный рост (100-250 см):")
            return

        await state.update_data(height_cm=height_cm)

        await callback.answer(
            f"✅ Рост: {height_cm:.0f} см\n\n"
            f"Теперь введите ваш **вес в килограммах** (например: 75.5):"
        )
        await state.set_state(SettingsStates.waiting_for_weight)

    except ValueError:
        await callback.answer("⚠️ Пожалуйста, введите число:")


@router.message(SettingsStates.waiting_for_weight)
async def settings_weight_received(callback: Message, state: FSMContext):
    """Handle weight input."""
    try:
        weight_text = callback.text.strip().replace(",", ".")
        weight_kg = float(weight_text)

        if weight_kg < 30 or weight_kg > 300:
            await callback.answer("⚠️ Пожалуйста, введите реальный вес (30-300 кг):")
            return

        await state.update_data(weight_kg=weight_kg)

        await callback.answer(
            f"✅ Вес: {weight_kg:.1f} кг\n\n"
            f"Последний параметр! Укажите уровень вашей активности:\n\n"
            f"1 - Сидячий образ жизни\n"
            f"2 - Легкая активность (1-3 раза в неделю)\n"
            f"3 - Умеренная активность (3-5 раз в неделю)\n"
            f"4 - Высокая активность (6-7 раз в неделю)\n"
            f"5 - Очень высокая (2 раза в день)\n\n"
            f"Введите число от 1 до 5:"
        )
        await state.set_state(SettingsStates.waiting_for_activity)

    except ValueError:
        await callback.answer("⚠️ Пожалуйста, введите число:")


@router.message(SettingsStates.waiting_for_activity)
async def settings_activity_received(callback: Message, state: FSMContext):
    """Handle activity level input and save all physical parameters."""
    try:
        activity_input = int(callback.text.strip())

        activity_map = {
            1: "sedentary",
            2: "lightly_active",
            3: "moderately_active",
            4: "very_active",
            5: "extremely_active"
        }

        activity_level = activity_map.get(activity_input)

        if not activity_level:
            await callback.answer("⚠️ Пожалуйста, введите число от 1 до 5:")
            return

        # Get all data
        data = await state.get_data()

        # Save to database via agent-api
        telegram_id = callback.from_user.id
        import httpx
        http_client = httpx.AsyncClient(timeout=30.0)

        url = f"{app_settings.AGENT_API_URL}/v1/users/{telegram_id}/physical"
        response = await http_client.put(
            url,
            json={
                "age": data.get('age'),
                "gender": data.get('gender'),
                "height_cm": data.get('height_cm'),
                "weight_kg": data.get('weight_kg'),
                "activity_level": activity_level
            }
        )
        response.raise_for_status()

        activity_display = {
            "sedentary": "Сидячий",
            "lightly_active": "Легкая",
            "moderately_active": "Умеренная",
            "very_active": "Высокая",
            "extremely_active": "Очень высокая"
        }

        await callback.answer(
            f"✅ **Физические параметры сохранены!**\n\n"
            f"👤 **Ваши данные:**\n"
            f"• Возраст: {data.get('age')} лет\n"
            f"• Пол: {'Мужской' if data.get('gender') == 'male' else 'Женский'}\n"
            f"• Рост: {data.get('height_cm'):.0f} см\n"
            f"• Вес: {data.get('weight_kg'):.1f} кг\n"
            f"• Активность: {activity_display.get(activity_level)}\n\n"
            f"Вес добавлен в историю для отслеживания прогресса!\n\n"
            f"Используйте /weight для обновления веса.",
            parse_mode="Markdown"
        )

        # Clear state
        await state.clear()

    except ValueError:
        await callback.answer("⚠️ Пожалуйста, введите число от 1 до 5:")
    except Exception as e:
        logger.error(f"Error saving physical parameters: {e}")
        await callback.answer("❌ Произошла ошибка при сохранении.")
        await state.clear()


@router.callback_query(F.data == "settings_goals")
async def settings_configure_goals(callback: CallbackQuery, state: FSMContext):
    """Handle KBJU goals configuration."""
    await callback.answer()

    await callback.message.edit_text(
        "🎯 **Настройка целей по КБЖУ**\n\n"
        "Сначала выберите вашу цель:",
        reply_markup=get_goal_selection_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(SettingsStates.waiting_for_goal_selection)


@router.callback_query(F.data.startswith("goal_"))
async def settings_goal_selected(callback: CallbackQuery, state: FSMContext):
    """Handle goal selection."""
    await callback.answer()

    goal = callback.data.replace("goal_", "")
    await state.update_data(selected_goal=goal)

    goal_names = {
        "weight_loss": "Похудение",
        "muscle_gain": "Набор мышечной массы",
        "maintenance": "Поддержание веса",
        "health": "Здоровье"
    }

    await callback.message.edit_text(
        f"✅ Выбрана цель: **{goal_names.get(goal, goal)}**\n\n"
        f"Теперь введите ваш **дневной лимит калорий** (например: 2000):",
        parse_mode="Markdown"
    )
    await state.set_state(SettingsStates.waiting_for_calories)


@router.message(SettingsStates.waiting_for_calories)
async def settings_calories_received(message: Message, state: FSMContext):
    """Handle calories input."""
    try:
        calories = int(message.text.strip())

        if calories < 800 or calories > 5000:
            await message.answer(
                "⚠️ Пожалуйста, введите реалистичное значение калорий (800-5000):"
            )
            return

        await state.update_data(target_calories=calories)

        await message.answer(
            f"✅ Калории: {calories} ккал\n\n"
            f"Теперь введите **цель по белкам** в граммах (например: 150):"
        )
        await state.set_state(SettingsStates.waiting_for_protein)

    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите число:")


@router.message(SettingsStates.waiting_for_protein)
async def settings_protein_received(message: Message, state: FSMContext):
    """Handle protein input."""
    try:
        protein = int(message.text.strip())

        if protein < 0 or protein > 500:
            await message.answer(
                "⚠️ Пожалуйста, введите реалистичное значение белка (0-500г):"
            )
            return

        await state.update_data(target_protein=protein)

        await message.answer(
            f"✅ Белок: {protein}г\n\n"
            f"Теперь введите **цель по углеводам** в граммах (например: 200):"
        )
        await state.set_state(SettingsStates.waiting_for_carbs)

    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите число:")


@router.message(SettingsStates.waiting_for_carbs)
async def settings_carbs_received(message: Message, state: FSMContext):
    """Handle carbs input."""
    try:
        carbs = int(message.text.strip())

        if carbs < 0 or carbs > 700:
            await message.answer(
                "⚠️ Пожалуйста, введите реалистичное значение углеводов (0-700г):"
            )
            return

        await state.update_data(target_carbs=carbs)

        await message.answer(
            f"✅ Углеводы: {carbs}г\n\n"
            f"Теперь введите **цель по жирам** в граммах (например: 60):"
        )
        await state.set_state(SettingsStates.waiting_for_fat)

    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите число:")


@router.message(SettingsStates.waiting_for_fat)
async def settings_fat_received(message: Message, state: FSMContext):
    """Handle fat input and save all goals."""
    try:
        fat = int(message.text.strip())

        if fat < 0 or fat > 300:
            await message.answer(
                "⚠️ Пожалуйста, введите реалистичное значение жиров (0-300г):"
            )
            return

        # Get all data
        data = await state.get_data()
        data['target_fat'] = fat

        # Save to database via agent-api
        telegram_id = message.from_user.id
        success = await agent_client.update_user_goals(
            telegram_id=telegram_id,
            goal=data.get('selected_goal'),
            target_calories=data.get('target_calories'),
            target_protein=data.get('target_protein'),
            target_carbs=data.get('target_carbs'),
            target_fat=fat
        )

        if success:
            await message.answer(
                f"✅ **Ваши цели сохранены!**\n\n"
                f"📊 **Дневные цели:**\n"
                f"• Калории: {data.get('target_calories')} ккал\n"
                f"• Белки: {data.get('target_protein')}г\n"
                f"• Углеводы: {data.get('target_carbs')}г\n"
                f"• Жиры: {fat}г\n\n"
                f"Теперь ваши отчёты будут показывать прогресс к этим целям!",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "❌ Не удалось сохранить настройки. Попробуйте позже."
            )

        # Clear state
        await state.clear()

    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите число:")
    except Exception as e:
        logger.error(f"Error saving goals: {e}")
        await message.answer("❌ Произошла ошибка при сохранении.")
        await state.clear()


# DISABLED: FatSecret connection callback - feature not supported
#
# @router.callback_query(F.data == "settings_fatsecret")
# async def settings_connect_fatsecret(callback: CallbackQuery):
#     """
#     DISABLED: FatSecret account connection not supported.
#     """
#     await callback.answer()
#     await callback.message.edit_text(
#         "ℹ️ **Подключение FatSecret недоступно**\n\n"
#         "FatSecret API не поддерживает подключение пользовательских аккаунтов.\n\n"
#         "Используйте настройки выше для ручной установки целей.",
#         parse_mode="Markdown"
#     )


@router.callback_query(F.data == "settings_back")
async def settings_back(callback: CallbackQuery):
    """Return to main settings menu."""
    await callback.answer()

    telegram_id = callback.from_user.id
    profile = await agent_client.get_user_profile(telegram_id)

    if profile:
        current_goals = _format_goals(profile)
        await callback.message.edit_text(
            f"⚙️ **Ваши текущие настройки**\n\n"
            f"{current_goals}\n\n"
            f"Что хотите настроить?",
            reply_markup=get_settings_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось загрузить настройки."
        )


def _format_goals(profile: dict) -> str:
    """Format user goals and physical parameters for display."""
    goal_names = {
        "weight_loss": "Похудение",
        "muscle_gain": "Набор мышечной массы",
        "maintenance": "Поддержание веса",
        "health": "Здоровье"
    }

    activity_names = {
        "sedentary": "Сидячий",
        "lightly_active": "Легкая",
        "moderately_active": "Умеренная",
        "very_active": "Высокая",
        "extremely_active": "Очень высокая"
    }

    goals_text = ""

    # Physical parameters section
    age = profile.get('age')
    gender = profile.get('gender')
    height = profile.get('height_cm')
    weight = profile.get('weight_kg')
    activity = profile.get('activity_level')

    if age or gender or height or weight or activity:
        goals_text += "👤 **Физические параметры:**\n"
        if age:
            goals_text += f"• Возраст: {age} лет\n"
        if gender:
            gender_display = "Мужской" if gender == "male" else "Женский" if gender == "female" else gender
            goals_text += f"• Пол: {gender_display}\n"
        if height:
            goals_text += f"• Рост: {height:.0f} см\n"
        if weight:
            goals_text += f"• Вес: {weight:.1f} кг\n"
        if activity:
            goals_text += f"• Активность: {activity_names.get(activity, activity)}\n"
        goals_text += "\n"

    # Goals section
    goal = profile.get('goal')
    goal_display = goal_names.get(goal, "Не установлена") if goal else "Не установлена"

    goals_text += f"🎯 **Цель:** {goal_display}\n\n"

    calories = profile.get('target_calories')
    protein = profile.get('target_protein')
    carbs = profile.get('target_carbs')
    fat = profile.get('target_fat')

    if calories or protein or carbs or fat:
        goals_text += "📊 **Дневные цели по КБЖУ:**\n"
        if calories:
            goals_text += f"• Калории: {calories} ккал\n"
        if protein:
            goals_text += f"• Белки: {protein}г\n"
        if carbs:
            goals_text += f"• Углеводы: {carbs}г\n"
        if fat:
            goals_text += f"• Жиры: {fat}г\n"
    else:
        goals_text += "📊 **Цели по КБЖУ:** Не установлены\n"

    return goals_text
