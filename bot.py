import os
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, CallbackQueryHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

# In-memory storage for requests
break_requests = {}

# States for conversation handler
DEPARTMENT, DURATION, AWAITING_APPROVAL = range(3)

# Define possible responses
DEPARTMENTS = [["AML"], ["Verification"], ["Alert"]]
DURATIONS = [["5", "10"], ["15", "20"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for their department."""
    user = update.message.from_user
    logger.info(f"User {user.id} started the bot")
    
    await update.message.reply_text(
        "Welcome to the Break Request Bot! 🔄\n"
        "Please choose your department:",
        reply_markup=ReplyKeyboardMarkup(DEPARTMENTS, one_time_keyboard=True)
    )
    return DEPARTMENT

async def choose_department(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the department and ask for break duration."""
    user = update.message.from_user
    department = update.message.text
    logger.info(f"Department of {user.id}: {department}")

    if department not in ["AML", "Verification", "Alert"]:
        await update.message.reply_text(
            "Please choose a valid department using the keyboard buttons provided.",
            reply_markup=ReplyKeyboardMarkup(DEPARTMENTS, one_time_keyboard=True)
        )
        return DEPARTMENT

    context.user_data['department'] = department
    await update.message.reply_text(
        f"You selected: {department}\n"
        "Now, please select your break duration in minutes:",
        reply_markup=ReplyKeyboardMarkup(DURATIONS, one_time_keyboard=True)
    )
    return DURATION


# First, modify the choose_duration function to add the Ignore button:
async def choose_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the duration and forward the request for approval."""
    user = update.message.from_user
    duration = update.message.text
    logger.info(f"Duration of {user.id}: {duration}")

    if not duration.isdigit() or int(duration) not in [5, 10, 15, 20]:
        await update.message.reply_text(
            "Please select a valid duration (5, 10, 15, or 20 minutes) using the keyboard buttons provided.",
            reply_markup=ReplyKeyboardMarkup(DURATIONS, one_time_keyboard=True)
        )
        return DURATION

    duration = int(duration)
    department = context.user_data['department']
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name

    # Store the request in memory
    break_requests[user_id] = {
        'username': username,
        'department': department,
        'duration': duration,
        'status': 'Pending'
    }

    # Create the approval message
    notification_text = (
        f"🔔 New Break Request\n\n"
        f"👤 User: @{username}\n"
        f"🏢 Department: {department}\n"
        f"⏱️ Duration: {duration} minutes\n\n"
        "Please approve or ignore this request."
    )
    
    # Add both Approve and Ignore buttons
    buttons = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve-{user_id}"),
            InlineKeyboardButton("❌ Ignore", callback_data=f"ignore-{user_id}")
        ]
    ]

    try:
        # Send request to approvers group
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=notification_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # Confirm to user
        await update.message.reply_text(
            "✅ Your break request has been sent for approval.\n"
            "Please wait for confirmation.",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"Break request sent for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to send break request: {e}")
        await update.message.reply_text(
            "❌ Sorry, there was an error processing your request.\n"
            "Please try again later or contact support.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    return AWAITING_APPROVAL





async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    user = update.message.from_user
    logger.info(f"User {user.id} canceled the conversation.")
    
    await update.message.reply_text(
        '❌ Break request cancelled.\n'
        'You can start a new request with /start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the chat ID of the current chat."""
    chat_id = update.effective_chat.id
    logger.info(f"Chat ID requested: {chat_id}")
    await update.message.reply_text(f"📝 The chat ID for this chat is: {chat_id}")

async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Timeout handler for the conversation."""
    await update.message.reply_text(
        '⏳ Break request timed out.\n'
        'Please start a new request with /start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def handle_request_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle both approve and ignore responses."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button click immediately
    
    try:
        # Extract action and user_id from callback data
        action, user_id = query.data.split('-')
        user_id = int(user_id)
        approver = query.from_user.username or query.from_user.first_name
        
        logger.info(f"Processing {action} for user_id: {user_id} by {approver}")
        
        if user_id in break_requests and break_requests[user_id]['status'] == 'Pending':
            username = break_requests[user_id]['username']
            duration = break_requests[user_id]['duration']

            if action == "approve":
                # Update request status
                break_requests[user_id]['status'] = 'Approved'

                # Update approval message
                await query.edit_message_text(
                    f"✅ Break Request Approved\n\n"
                    f"👤 User: @{username}\n"
                    f"⏱️ Duration: {duration} minutes\n"
                    f"👮 Approved by: @{approver}"
                )

                # Notify the employee
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"✅ Your break request has been approved!\n"
                             f"Duration: {duration} minutes\n"
                             "Enjoy your break! ☕\n\n"
                             "You can request another break with /start",
                        reply_markup=ReplyKeyboardRemove()
                    )
                    logger.info(f"Successfully notified user {user_id} of approval")
                except Exception as e:
                    logger.error(f"Failed to notify user {user_id} of approval: {e}")

            elif action == "ignore":
                # Update request status
                break_requests[user_id]['status'] = 'Ignored'

                # Update message to show ignored status
                await query.edit_message_text(
                    f"❌ Break Request Ignored\n\n"
                    f"👤 User: @{username}\n"
                    f"⏱️ Duration: {duration} minutes\n"
                    f"👮 Ignored by: @{approver}"
                )

                # Notify the employee
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="❌ Your break request has been declined.\n"
                             "You can submit a new request with /start",
                        reply_markup=ReplyKeyboardRemove()
                    )
                    logger.info(f"Successfully notified user {user_id} of ignored request")
                except Exception as e:
                    logger.error(f"Failed to notify user {user_id} of ignored request: {e}")
            
            # Clear the user data after processing
            if context.user_data:
                context.user_data.clear()
            
        else:
            logger.warning(f"Invalid or already processed request for user_id: {user_id}")
            await query.edit_message_text("⚠️ This request is no longer valid or has already been processed.")
            
    except Exception as e:
        logger.error(f"Error in handle_request_response: {e}")
        try:
            await query.edit_message_text("⚠️ An error occurred while processing this request.")
        except Exception as inner_e:
            logger.error(f"Failed to send error message: {inner_e}")

def main() -> None:
    """Start the bot."""
    try:
        # Create the Application
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers in the correct order
        # First add the global callback handler
        application.add_handler(
            CallbackQueryHandler(handle_request_response, pattern=r'^(approve|ignore)-\d+$')
        )

        # Then add conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                DEPARTMENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, choose_department)
                ],
                DURATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, choose_duration)
                ],
                AWAITING_APPROVAL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: AWAITING_APPROVAL)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', cancel)
            ],
            conversation_timeout=300,
            name="break_request_conversation",
            allow_reentry=True
        )

        # Add the conversation handler
        application.add_handler(conv_handler)
        
        # Add utility commands
        application.add_handler(CommandHandler("getchatid", get_chat_id))

        # Start the bot
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

 
if __name__ == '__main__':
    main()