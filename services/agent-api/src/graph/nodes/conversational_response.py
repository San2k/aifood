"""
LangGraph Node: conversational_response
Handles conversational interactions - questions, chat, and report requests.
"""

import logging
from typing import Dict, Any
from datetime import datetime, date, timedelta

from ..state import NutritionBotState
from ...services.llm_service import llm_service
from ...db.session import AsyncSessionLocal
from ...db.repositories.user_repository import UserRepository
from ...db.repositories.food_log_repository import FoodLogRepository

logger = logging.getLogger(__name__)


async def conversational_response(state: NutritionBotState) -> Dict[str, Any]:
    """
    Generate conversational response for non-food-logging intents.

    Handles:
    - view_report: Direct user to /today or /week commands
    - question: Answer nutrition-related questions
    - chat: Friendly greetings and small talk

    Args:
        state: Current graph state

    Returns:
        State updates with conversational response
    """
    raw_input = state.get("raw_input", "")
    detected_intent = state.get("detected_intent", "chat")
    user_id = state.get("user_id")

    logger.info(f"Generating conversational response for intent: {detected_intent}")

    try:
        # Special handling for view_report - fetch and display actual report
        if detected_intent == "view_report" and user_id:
            logger.info(f"Analyzing report request: {raw_input}")

            # Use LLM to understand what time period the user wants
            time_period_analysis = await llm_service.analyze_report_request(raw_input)

            period_type = time_period_analysis.get("period", "today")  # today, week, all, yesterday, etc.
            days_count = time_period_analysis.get("days", 1)

            logger.info(f"Detected time period: {period_type}, days: {days_count}")

            # Determine date range based on period type
            today = date.today()

            if period_type == "yesterday":
                target_date = today - timedelta(days=1)
                start_date = target_date
                end_date = target_date
                report_title = "вчера"
            elif period_type == "week":
                start_date = today - timedelta(days=6)
                end_date = today
                report_title = "за неделю"
            elif period_type == "all":
                start_date = today - timedelta(days=days_count - 1)
                end_date = today
                report_title = f"за последние {days_count} дней"
            elif period_type == "days":
                start_date = today - timedelta(days=days_count - 1)
                end_date = today
                report_title = f"за последние {days_count} {'день' if days_count == 1 else 'дней' if days_count < 5 else 'дней'}"
            else:  # today
                start_date = today
                end_date = today
                report_title = "за сегодня"

            async with AsyncSessionLocal() as session:
                food_log_repo = FoodLogRepository(session)
                user_repo = UserRepository(session)

                # Get user for targets
                user = await user_repo.get_by_id(user_id)

                # For single day reports
                if start_date == end_date:
                    # Get single day totals and entries
                    totals = await food_log_repo.calculate_daily_totals(user_id, start_date)
                    entries = await food_log_repo.get_entries_by_date(user_id, start_date)

                    calories = totals.get("calories", 0)
                    protein = totals.get("protein", 0)
                    carbs = totals.get("carbohydrates", 0)
                    fat = totals.get("fat", 0)

                    if len(entries) > 0:
                        formatted_text = f"📊 **Отчёт {report_title}**\n\n"

                        # Show individual food entries
                        formatted_text += "🍽 **Что вы съели:**\n"
                        for idx, entry in enumerate(entries, 1):
                            food_name = entry.food_name
                            serving_desc = entry.serving_description or ""
                            num_servings = entry.number_of_servings or 1
                            entry_cals = entry.calories or 0

                            # Format serving info
                            if num_servings > 1:
                                serving_info = f"{num_servings:.0f}x {serving_desc}" if serving_desc else f"{num_servings:.0f} порций"
                            else:
                                serving_info = serving_desc or "1 порция"

                            formatted_text += f"{idx}. {food_name} ({serving_info}) - {entry_cals:.0f} ккал\n"

                        # Show totals
                        formatted_text += f"\n📈 **Итого:**\n"

                        if user and user.target_calories:
                            calories_pct = (calories / user.target_calories * 100) if user.target_calories > 0 else 0
                            formatted_text += f"🔥 Калории: {calories:.0f} / {user.target_calories} ккал ({calories_pct:.0f}%)\n"
                        else:
                            formatted_text += f"🔥 Калории: {calories:.0f} ккал\n"

                        if user and user.target_protein:
                            protein_pct = (protein / user.target_protein * 100) if user.target_protein > 0 else 0
                            formatted_text += f"🥩 Белки: {protein:.0f} / {user.target_protein}г ({protein_pct:.0f}%)\n"
                        else:
                            formatted_text += f"🥩 Белки: {protein:.0f}г\n"

                        if user and user.target_carbs:
                            carbs_pct = (carbs / user.target_carbs * 100) if user.target_carbs > 0 else 0
                            formatted_text += f"🍞 Углеводы: {carbs:.0f} / {user.target_carbs}г ({carbs_pct:.0f}%)\n"
                        else:
                            formatted_text += f"🍞 Углеводы: {carbs:.0f}г\n"

                        if user and user.target_fat:
                            fat_pct = (fat / user.target_fat * 100) if user.target_fat > 0 else 0
                            formatted_text += f"🥑 Жиры: {fat:.0f} / {user.target_fat}г ({fat_pct:.0f}%)\n"
                        else:
                            formatted_text += f"🥑 Жиры: {fat:.0f}г\n"

                        logger.info(f"Generated single-day report for user {user_id} with {len(entries)} entries")

                        return {
                            "ai_advice": formatted_text,
                            "should_end": True,
                            "updated_at": datetime.utcnow()
                        }
                    else:
                        return {
                            "ai_advice": f"📊 Дневник {report_title} пуст.\n\nЗапишите что вы съели, например: 'съел яблоко'",
                            "should_end": True,
                            "updated_at": datetime.utcnow()
                        }

                else:
                    # Multi-day report
                    formatted_text = f"📊 **Отчёт {report_title}**\n\n"

                    total_calories = 0.0
                    total_protein = 0.0
                    total_carbs = 0.0
                    total_fat = 0.0
                    days_with_data = 0
                    total_entries = 0

                    # Collect days with entries
                    days_data = []

                    current_date = start_date
                    while current_date <= end_date:
                        day_totals = await food_log_repo.calculate_daily_totals(user_id, current_date)
                        day_entries = await food_log_repo.get_entries_by_date(user_id, current_date)

                        day_calories = day_totals.get("calories", 0)

                        if day_calories > 0 or len(day_entries) > 0:
                            days_with_data += 1
                            total_calories += day_calories
                            total_protein += day_totals.get("protein", 0)
                            total_carbs += day_totals.get("carbohydrates", 0)
                            total_fat += day_totals.get("fat", 0)
                            total_entries += len(day_entries)

                            days_data.append({
                                "date": current_date,
                                "entries": day_entries,
                                "totals": day_totals,
                                "calories": day_calories
                            })

                        current_date += timedelta(days=1)

                    if days_with_data > 0:
                        # Show entries for each day
                        for day_data in days_data:
                            day_date = day_data["date"]
                            day_entries = day_data["entries"]
                            day_calories = day_data["calories"]

                            day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][day_date.weekday()]
                            formatted_text += f"📅 **{day_name} ({day_date.day}.{day_date.month})** - {day_calories:.0f} ккал\n"

                            # Show food entries for this day
                            for idx, entry in enumerate(day_entries, 1):
                                food_name = entry.food_name
                                serving_desc = entry.serving_description or ""
                                num_servings = entry.number_of_servings or 1
                                entry_cals = entry.calories or 0

                                # Format serving info
                                if num_servings > 1:
                                    serving_info = f"{num_servings:.0f}x {serving_desc}" if serving_desc else f"{num_servings:.0f} порций"
                                else:
                                    serving_info = serving_desc or "1 порция"

                                formatted_text += f"  • {food_name} ({serving_info}) - {entry_cals:.0f} ккал\n"

                            formatted_text += "\n"

                        # Show averages
                        avg_calories = total_calories / days_with_data
                        avg_protein = total_protein / days_with_data
                        avg_carbs = total_carbs / days_with_data
                        avg_fat = total_fat / days_with_data

                        formatted_text += f"📈 **Средние значения за {days_with_data} {'день' if days_with_data == 1 else 'дня' if days_with_data < 5 else 'дней'}:**\n"
                        formatted_text += f"🔥 Калории: {avg_calories:.0f} ккал/день\n"
                        formatted_text += f"🥩 Белки: {avg_protein:.0f}г/день\n"
                        formatted_text += f"🍞 Углеводы: {avg_carbs:.0f}г/день\n"
                        formatted_text += f"🥑 Жиры: {avg_fat:.0f}г/день\n"

                        if user and user.target_calories:
                            adherence = (avg_calories / user.target_calories * 100) if user.target_calories > 0 else 0
                            formatted_text += f"\n✅ **Выполнение цели:** {adherence:.0f}%"

                        logger.info(f"Generated multi-day report for user {user_id}: {days_count} days, {days_with_data} with data")

                        return {
                            "ai_advice": formatted_text,
                            "should_end": True,
                            "updated_at": datetime.utcnow()
                        }
                    else:
                        return {
                            "ai_advice": f"📊 Нет записей {report_title}.\n\nЗапишите что вы съели, например: 'съел яблоко'",
                            "should_end": True,
                            "updated_at": datetime.utcnow()
                        }

        # Get user context if available
        user_context = None
        if user_id:
            # TODO: Load user profile from database for personalized responses
            # For now, use basic context
            user_context = {
                "goal": "maintenance",
                "target_calories": 2000
            }

        # Generate response using LLM for questions and chat
        response_text = await llm_service.generate_conversational_response(
            user_input=raw_input,
            intent=detected_intent,
            user_context=user_context
        )

        logger.info(f"Generated conversational response: {response_text[:100]}...")

        return {
            "ai_advice": response_text,  # Reuse ai_advice field for conversational responses
            "should_end": True,  # End graph after conversational response
            "updated_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error generating conversational response: {e}", exc_info=True)

        # Provide helpful fallback message
        fallback_messages = {
            "view_report": "Для просмотра дневника используйте:\n• /today - сегодняшний отчёт\n• /week - недельный отчёт",
            "question": "Извините, не могу ответить на этот вопрос сейчас. Попробуйте позже или используйте /help.",
            "chat": "Здравствуйте! Я помогу вам отслеживать питание. Просто напишите что вы съели, например: 'съел 2 яйца'."
        }

        fallback_text = fallback_messages.get(detected_intent, "Используйте /help для справки.")

        return {
            "ai_advice": fallback_text,
            "should_end": True,
            "errors": state.get("errors", []) + [f"Conversational response error: {str(e)}"],
            "updated_at": datetime.utcnow()
        }
