import os
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, CallbackQueryHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

# In-memory storage for requests
break_requests = {}

# States for conversation handler
DEPARTMENT, DURATION, AWAITING_APPROVAL = range(3)

# Define possible responses
DEPARTMENTS = [["AML"], ["Verification"], ["Alert"]]
DURATIONS = [["5", "10"], ["15", "20"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Please choose your department:", 
        reply_markup=ReplyKeyboardMarkup(DEPARTMENTS, one_time_keyboard=True)
    )
    return DEPARTMENT

async def choose_department(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['department'] = update.message.text
    await update.message.reply_text(
        "Please select break duration in minutes:", 
        reply_markup=ReplyKeyboardMarkup(DURATIONS, one_time_keyboard=True)
    )
    return DURATION

async def choose_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    duration = int(update.message.text)
    department = context.user_data['department']
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name

    # Store the request in-memory
    break_requests[user_id] = {
        'username': username,
        'department': department,
        'duration': duration,
        'status': 'Pending'
    }

    # Send request to division heads
    notification_text = (f"Break Request:\nUser: @{username}\n"
                         f"Department: {department}\n"
                         f"Duration: {duration} minutes\n"
                         "Approve this request?")
    buttons = [[InlineKeyboardButton("Approve", callback_data=f"approve-{user_id}")]]
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID, 
        text=notification_text, 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    await update.message.reply_text("Your request has been sent for approval.")
    return AWAITING_APPROVAL

async def approve_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split('-')[1])

    # Approve request in memory
    if user_id in break_requests and break_requests[user_id]['status'] == 'Pending':
        break_requests[user_id]['status'] = 'Approved'
        await query.edit_message_text(f"Request by @{break_requests[user_id]['username']} approved.")

        # Notify the employee
        await context.bot.send_message(
            chat_id=user_id, 
            text=f"Your break for {break_requests[user_id]['duration']} minutes has been approved. Enjoy your break!"
        )
    else:
        await query.edit_message_text("Request already approved or invalid.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Request cancelled.")
    return ConversationHandler.END

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DEPARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_department)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_duration)],
            AWAITING_APPROVAL: [CallbackQueryHandler(approve_request, pattern=r"^approve-\d+$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
