"""Module for handling leaderboard functionality."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_all_results, get_user_result, format_display_name
from .messages import handle_group_message  # Import from the same package

logger = logging.getLogger(__name__)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the current leaderboard of best results, filtered by user's skill group."""
    if await handle_group_message(update, context):
        return
        
    user_id = update.message.from_user.id
    user_result = get_user_result(user_id)
    
    results = get_all_results()
    
    if not results:
        await update.message.reply_text("Пока нет результатов для отображения.")
        return
    
    # Determine user's group
    user_group = "Любители"  # Default group if user has no results
    if user_result:
        best_series = user_result[4]  # Updated index for best_series
        if best_series >= 93:
            user_group = "Профи"
        elif best_series >= 80:
            user_group = "Продвинутые"
        else:
            user_group = "Любители"
    
    # Filter results based on user's group
    if user_group == "Профи":
        filtered_results = [r for r in results if r[4] >= 93]  # Updated index for best_series
        group_title = "🏆 Группа Профи 🏆"
    elif user_group == "Продвинутые":
        filtered_results = [r for r in results if 80 <= r[4] <= 92]  # Updated index for best_series
        group_title = "🏆 Группа Продвинутые 🏆"
    else:  # Любители
        filtered_results = [r for r in results if r[4] <= 79]  # Updated index for best_series
        group_title = "🏆 Группа Любители 🏆"
    
    # Sort results by best_series (descending) and then by total_tens (descending)
    sorted_results = sorted(filtered_results, key=lambda x: (x[4], x[5]), reverse=True)  # Updated indexes
    
    # Format the leaderboard message
    leaderboard_text = f"{group_title}\n\n"
    
    if not sorted_results:
        leaderboard_text += "В этой группе пока нет результатов."
    else:
        for i, result in enumerate(sorted_results[:50], 1):  # Show top 50 results
            # Unpack new result format
            _, first_name, last_name, _, best_series, total_tens = result
            display_name = format_display_name(first_name, last_name)
            
            name_display = display_name[:20] + "..." if len(display_name) > 20 else display_name
            if user_group == "Профи":
                leaderboard_text += f"{i}. {name_display}: {best_series}-{total_tens}x\n"
            else:
                leaderboard_text += f"{i}. {name_display}: {best_series}-{total_tens}\n"
    
    await update.message.reply_text(leaderboard_text)

async def leaderboard_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display top 10 results for each of the three skill groups."""
    if await handle_group_message(update, context):
        return
        
    results = get_all_results()
    
    if not results:
        await update.message.reply_text("Пока нет результатов для отображения.")
        return
    
    # Filter results into three groups
    pro_results = [r for r in results if r[4] >= 93]  # Updated index for best_series
    semi_pro_results = [r for r in results if 80 <= r[4] < 93]  # Updated index for best_series
    amateur_results = [r for r in results if r[4] < 80]  # Updated index for best_series
    
    # Sort each group by best_series and total_tens
    pro_sorted = sorted(pro_results, key=lambda x: (x[4], x[5]), reverse=True)[:30]  # Updated indexes
    semi_pro_sorted = sorted(semi_pro_results, key=lambda x: (x[4], x[5]), reverse=True)[:30]  # Updated indexes
    amateur_sorted = sorted(amateur_results, key=lambda x: (x[4], x[5]), reverse=True)[:30]  # Updated indexes
    
    # Format the message
    leaderboard_text = "🏆 Таблица лидеров по всем группам 🏆\n\n"
    
    # Pro group
    leaderboard_text += "👑 Группа Профи 👑\n"
    if not pro_sorted:
        leaderboard_text += "В этой группе пока нет результатов.\n\n"
    else:
        for i, result in enumerate(pro_sorted, 1):
            # Unpack new result format
            _, first_name, last_name, _, best_series, total_tens = result
            display_name = format_display_name(first_name, last_name)
            
            name_display = display_name[:20] + "..." if len(display_name) > 20 else display_name
            leaderboard_text += f"{i}. {name_display}: {best_series}-{total_tens}x\n"
        leaderboard_text += "\n"
    
    # Semi-pro group
    leaderboard_text += "🥈 Группа Продвинутые 🥈\n"
    if not semi_pro_sorted:
        leaderboard_text += "В этой группе пока нет результатов.\n\n"
    else:
        for i, result in enumerate(semi_pro_sorted, 1):
            # Unpack new result format
            _, first_name, last_name, _, best_series, total_tens = result
            display_name = format_display_name(first_name, last_name)
            
            name_display = display_name[:20] + "..." if len(display_name) > 20 else display_name
            leaderboard_text += f"{i}. {name_display}: {best_series}-{total_tens}\n"
        leaderboard_text += "\n"
    
    # Amateur group
    leaderboard_text += "🥉 Группа Любители 🥉\n"
    if not amateur_sorted:
        leaderboard_text += "В этой группе пока нет результатов.\n\n"
    else:
        for i, result in enumerate(amateur_sorted, 1):
            # Unpack new result format
            _, first_name, last_name, _, best_series, total_tens = result
            display_name = format_display_name(first_name, last_name)
            
            name_display = display_name[:20] + "..." if len(display_name) > 20 else display_name
            leaderboard_text += f"{i}. {name_display}: {best_series}-{total_tens}\n"
    
    await update.message.reply_text(leaderboard_text)
