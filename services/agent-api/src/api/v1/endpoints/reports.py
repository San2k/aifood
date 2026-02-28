"""
/v1/reports endpoints for daily and weekly reports.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import date, timedelta

from ....db.session import AsyncSessionLocal
from ....db.repositories.user_repository import UserRepository
from ....db.repositories.food_log_repository import FoodLogRepository

logger = logging.getLogger(__name__)

router = APIRouter()


def get_progress_indicator(percentage: float) -> str:
    """
    Get emoji indicator based on progress percentage.

    Args:
        percentage: Progress percentage (0-100+)

    Returns:
        Emoji indicator (✅/⚠️/❌)
    """
    if 90 <= percentage <= 110:
        return "✅"  # Green - perfect range
    elif 80 <= percentage < 90 or 110 < percentage <= 120:
        return "⚠️"  # Yellow - acceptable but not ideal
    else:
        return "❌"  # Red - too low or too high


def get_progress_bar(percentage: float, length: int = 10) -> str:
    """
    Generate visual progress bar using block characters.

    Args:
        percentage: Progress percentage (0-100+)
        length: Bar length in characters

    Returns:
        Progress bar string
    """
    filled = min(int(percentage / 100 * length), length)
    empty = length - filled

    # Use different characters based on progress
    if 90 <= percentage <= 110:
        bar = "█" * filled + "░" * empty
    elif percentage < 90:
        bar = "▓" * filled + "░" * empty
    else:  # > 110
        bar = "▓" * filled + "░" * empty

    return f"[{bar}]"


class DailyReportResponse(BaseModel):
    """Response schema for daily report."""

    success: bool
    date: date
    totals: Dict[str, float]
    entry_count: int
    target_calories: Optional[int] = None
    target_protein: Optional[int] = None
    target_carbs: Optional[int] = None
    target_fat: Optional[int] = None
    formatted_text: str


class WeeklyReportResponse(BaseModel):
    """Response schema for weekly report."""

    success: bool
    start_date: date
    end_date: date
    daily_totals: Dict[str, Dict[str, float]]  # date -> totals
    average_calories: float
    formatted_text: str


@router.get("/today/{telegram_id}", response_model=DailyReportResponse)
async def get_daily_report(telegram_id: int) -> DailyReportResponse:
    """
    Get daily nutrition report for today.

    Args:
        telegram_id: Telegram user ID

    Returns:
        Daily report with totals and formatted text
    """
    logger.info(f"Getting daily report for telegram_id {telegram_id}")

    try:
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            food_log_repo = FoodLogRepository(session)

            # Get user
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Get today's totals
            today = date.today()
            totals = await food_log_repo.calculate_daily_totals(user.id, today)
            entries = await food_log_repo.get_entries_by_date(user.id, today)

            # Format response text
            calories = totals.get("calories", 0)
            protein = totals.get("protein", 0)
            carbs = totals.get("carbohydrates", 0)
            fat = totals.get("fat", 0)

            formatted_text = f"📊 **Отчёт за сегодня** ({today.day}.{today.month}.{today.year})\n\n"

            # Calories with progress indicator
            if user.target_calories:
                calories_pct = (calories / user.target_calories * 100) if user.target_calories > 0 else 0
                indicator = get_progress_indicator(calories_pct)
                progress_bar = get_progress_bar(calories_pct)
                formatted_text += f"{indicator} **Калории:** {calories:.0f} / {user.target_calories} ккал ({calories_pct:.0f}%)\n"
                formatted_text += f"   {progress_bar}\n\n"
            else:
                formatted_text += f"🔥 **Калории:** {calories:.0f} ккал\n\n"

            # Protein with progress indicator
            if user.target_protein:
                protein_pct = (protein / user.target_protein * 100) if user.target_protein > 0 else 0
                indicator = get_progress_indicator(protein_pct)
                progress_bar = get_progress_bar(protein_pct)
                formatted_text += f"{indicator} **Белки:** {protein:.0f} / {user.target_protein}г ({protein_pct:.0f}%)\n"
                formatted_text += f"   {progress_bar}\n\n"
            else:
                formatted_text += f"🥩 **Белки:** {protein:.0f}г\n\n"

            # Carbs with progress indicator
            if user.target_carbs:
                carbs_pct = (carbs / user.target_carbs * 100) if user.target_carbs > 0 else 0
                indicator = get_progress_indicator(carbs_pct)
                progress_bar = get_progress_bar(carbs_pct)
                formatted_text += f"{indicator} **Углеводы:** {carbs:.0f} / {user.target_carbs}г ({carbs_pct:.0f}%)\n"
                formatted_text += f"   {progress_bar}\n\n"
            else:
                formatted_text += f"🍞 **Углеводы:** {carbs:.0f}г\n\n"

            # Fat with progress indicator
            if user.target_fat:
                fat_pct = (fat / user.target_fat * 100) if user.target_fat > 0 else 0
                indicator = get_progress_indicator(fat_pct)
                progress_bar = get_progress_bar(fat_pct)
                formatted_text += f"{indicator} **Жиры:** {fat:.0f} / {user.target_fat}г ({fat_pct:.0f}%)\n"
                formatted_text += f"   {progress_bar}\n\n"
            else:
                formatted_text += f"🥑 **Жиры:** {fat:.0f}г\n\n"

            # Summary
            formatted_text += f"📝 **Записей:** {len(entries)}"

            # Tips based on progress
            if len(entries) == 0:
                formatted_text += "\n\n💡 Пока нет записей за сегодня. Начните логировать!"
            elif user.target_calories:
                calories_pct = (calories / user.target_calories * 100) if user.target_calories > 0 else 0
                if calories_pct < 80:
                    remaining = user.target_calories - calories
                    formatted_text += f"\n\n💡 У вас ещё {remaining:.0f} ккал до цели"
                elif calories_pct > 110:
                    formatted_text += "\n\n⚠️ Вы превысили дневную цель по калориям"
                else:
                    formatted_text += "\n\n✨ Отличный прогресс! Продолжайте в том же духе!"

            return DailyReportResponse(
                success=True,
                date=today,
                totals=totals,
                entry_count=len(entries),
                target_calories=user.target_calories,
                target_protein=user.target_protein,
                target_carbs=user.target_carbs,
                target_fat=user.target_fat,
                formatted_text=formatted_text
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating daily report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/week/{telegram_id}", response_model=WeeklyReportResponse)
async def get_weekly_report(telegram_id: int) -> WeeklyReportResponse:
    """
    Get weekly nutrition report for last 7 days.

    Args:
        telegram_id: Telegram user ID

    Returns:
        Weekly report with daily totals and averages
    """
    logger.info(f"Getting weekly report for telegram_id {telegram_id}")

    try:
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            food_log_repo = FoodLogRepository(session)

            # Get user
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Get last 7 days
            end_date = date.today()
            start_date = end_date - timedelta(days=6)

            daily_totals = {}
            total_calories = 0.0
            total_protein = 0.0
            total_carbs = 0.0
            total_fat = 0.0
            days_with_data = 0

            current_date = start_date
            while current_date <= end_date:
                totals = await food_log_repo.calculate_daily_totals(user.id, current_date)
                daily_totals[str(current_date)] = totals

                calories = totals.get("calories", 0)
                if calories > 0:
                    total_calories += calories
                    total_protein += totals.get("protein", 0)
                    total_carbs += totals.get("carbohydrates", 0)
                    total_fat += totals.get("fat", 0)
                    days_with_data += 1

                current_date += timedelta(days=1)

            average_calories = total_calories / days_with_data if days_with_data > 0 else 0
            average_protein = total_protein / days_with_data if days_with_data > 0 else 0
            average_carbs = total_carbs / days_with_data if days_with_data > 0 else 0
            average_fat = total_fat / days_with_data if days_with_data > 0 else 0

            # Format response text
            formatted_text = f"📊 **Недельный отчёт**\n"
            formatted_text += f"_{start_date.day}.{start_date.month} - {end_date.day}.{end_date.month}.{end_date.year}_\n\n"

            # Daily calories breakdown
            formatted_text += "📅 **Калории по дням:**\n"
            day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

            current_date = start_date
            while current_date <= end_date:
                day_name = day_names[current_date.weekday()]
                totals = daily_totals[str(current_date)]
                calories = totals.get("calories", 0)

                # Visual bar for daily calories
                if user.target_calories and calories > 0:
                    day_pct = (calories / user.target_calories * 100) if user.target_calories > 0 else 0
                    mini_bar_length = min(int(day_pct / 100 * 5), 10)  # Mini bar 0-5 blocks
                    mini_bar = "▓" * mini_bar_length + "░" * (5 - mini_bar_length) if mini_bar_length <= 5 else "▓" * 5
                    formatted_text += f"{day_name} {current_date.day:2d}.{current_date.month:02d}: {mini_bar} {calories:4.0f} ккал\n"
                elif calories > 0:
                    formatted_text += f"{day_name} {current_date.day:2d}.{current_date.month:02d}: {calories:4.0f} ккал\n"
                else:
                    formatted_text += f"{day_name} {current_date.day:2d}.{current_date.month:02d}: —\n"

                current_date += timedelta(days=1)

            # Weekly averages
            formatted_text += f"\n📈 **Средние за неделю:**\n\n"

            # Calories average
            if user.target_calories:
                avg_cal_pct = (average_calories / user.target_calories * 100) if user.target_calories > 0 else 0
                indicator = get_progress_indicator(avg_cal_pct)
                progress_bar = get_progress_bar(avg_cal_pct)
                formatted_text += f"{indicator} **Калории:** {average_calories:.0f} / {user.target_calories} ккал/день ({avg_cal_pct:.0f}%)\n"
                formatted_text += f"   {progress_bar}\n\n"
            else:
                formatted_text += f"🔥 **Калории:** {average_calories:.0f} ккал/день\n\n"

            # Protein average
            if user.target_protein:
                avg_prot_pct = (average_protein / user.target_protein * 100) if user.target_protein > 0 else 0
                indicator = get_progress_indicator(avg_prot_pct)
                progress_bar = get_progress_bar(avg_prot_pct)
                formatted_text += f"{indicator} **Белки:** {average_protein:.0f} / {user.target_protein}г/день ({avg_prot_pct:.0f}%)\n"
                formatted_text += f"   {progress_bar}\n\n"
            else:
                formatted_text += f"🥩 **Белки:** {average_protein:.0f}г/день\n\n"

            # Carbs average
            if user.target_carbs:
                avg_carbs_pct = (average_carbs / user.target_carbs * 100) if user.target_carbs > 0 else 0
                indicator = get_progress_indicator(avg_carbs_pct)
                progress_bar = get_progress_bar(avg_carbs_pct)
                formatted_text += f"{indicator} **Углеводы:** {average_carbs:.0f} / {user.target_carbs}г/день ({avg_carbs_pct:.0f}%)\n"
                formatted_text += f"   {progress_bar}\n\n"
            else:
                formatted_text += f"🍞 **Углеводы:** {average_carbs:.0f}г/день\n\n"

            # Fat average
            if user.target_fat:
                avg_fat_pct = (average_fat / user.target_fat * 100) if user.target_fat > 0 else 0
                indicator = get_progress_indicator(avg_fat_pct)
                progress_bar = get_progress_bar(avg_fat_pct)
                formatted_text += f"{indicator} **Жиры:** {average_fat:.0f} / {user.target_fat}г/день ({avg_fat_pct:.0f}%)\n"
                formatted_text += f"   {progress_bar}\n\n"
            else:
                formatted_text += f"🥑 **Жиры:** {average_fat:.0f}г/день\n\n"

            # Summary insights
            formatted_text += f"📊 **Статистика:**\n"
            formatted_text += f"• Дней с записями: {days_with_data} / 7\n"

            if days_with_data == 0:
                formatted_text += "\n💡 Нет данных за эту неделю. Начните логировать!"
            elif user.target_calories:
                avg_cal_pct = (average_calories / user.target_calories * 100) if user.target_calories > 0 else 0
                if 90 <= avg_cal_pct <= 110:
                    formatted_text += "\n✨ Отличное соблюдение целей! Так держать!"
                elif avg_cal_pct < 90:
                    formatted_text += f"\n💡 Средние калории ниже цели. Возможно стоит добавить больше питательных продуктов"
                else:
                    formatted_text += f"\n⚠️ Средние калории выше цели. Попробуйте контролировать порции"

            return WeeklyReportResponse(
                success=True,
                start_date=start_date,
                end_date=end_date,
                daily_totals=daily_totals,
                average_calories=average_calories,
                formatted_text=formatted_text
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")
