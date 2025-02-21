import logging
import requests
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
import nest_asyncio
from datetime import datetime, timedelta

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables from .env file
load_dotenv()

# Get the bot token and allowed users from the environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "").split(",")))

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Toggle user authorization
USER_AUTHORIZATION_ENABLED = False

def is_user_allowed(user_id):
    if not USER_AUTHORIZATION_ENABLED:
        return True
    return user_id in ALLOWED_USERS

# Dictionary to store user guesses
user_guesses = {}

# Command to submit a guess
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Submit a guess for the Bitcoin price at the next meetup."""
    user = update.effective_user
    logger.info(f"Received /guess command from {user.full_name} (ID: {user.id})")
    
    try:
        guess_price = float(context.args[0])
        user_guesses[user.id] = guess_price
        await update.message.reply_text(f"Your guess of ${guess_price:.2f} has been recorded.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /guess <price>")

# Function to find the next meetup date
def get_next_meetup_date():
    today = datetime.today()
    first_day_current_month = today.replace(day=1)
    first_thursday_current_month = first_day_current_month + timedelta(days=(3 - first_day_current_month.weekday() + 7) % 7)
    second_thursday_current_month = first_thursday_current_month + timedelta(days=7)
    
    if today <= second_thursday_current_month:
        return second_thursday_current_month
    else:
        first_day_next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        first_thursday_next_month = first_day_next_month + timedelta(days=(3 - first_day_next_month.weekday() + 7) % 7)
        second_thursday_next_month = first_thursday_next_month + timedelta(days=7)
        return second_thursday_next_month
        
# Function to announce the winner
async def announce_winner(context: ContextTypes.DEFAULT_TYPE):
    next_meetup = get_next_meetup_date()
    response = requests.get("https://bitpay.com/api/rates/BTC/USD")
    price_data = response.json()
    btc_price = price_data['rate']
    
    closest_user = None
    closest_diff = float('inf')
    
    for user_id, guess in user_guesses.items():
        diff = abs(guess - btc_price)
        if diff < closest_diff:
            closest_diff = diff
            closest_user = user_id
    
    if closest_user:
        user = await context.bot.get_chat(closest_user)
        winner_message = f"🎉 The winner is {user.username} with a guess of ${user_guesses[closest_user]:.2f}! The actual price is ${btc_price:.2f}."
        await context.bot.send_message(chat_id=closest_user, text=winner_message)
    
    user_guesses.clear()

# Schedule the announcement
async def schedule_announcement(application):
    next_meetup = get_next_meetup_date()
    announcement_time = next_meetup.replace(hour=20, minute=0, second=0, microsecond=0)
    delay = (announcement_time - datetime.now()).total_seconds()
    application.job_queue.run_once(announce_winner, delay)

# Define the /nextmeetup command handler
async def nextmeetup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the date of the next meetup, which is always the second Thursday of the month."""
    user = update.effective_user
    logger.info(f"Received /nextmeetup command from {user.full_name} (ID: {user.id})")
    next_meetup = get_next_meetup_date()
    await update.message.reply_text(f"The next meetup is on {next_meetup.strftime('%A %B %d, %Y')}.")

# Define the /price command handler
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the current price of Bitcoin in USD."""
    user = update.effective_user
    logger.info(f"Received /price command from {user.full_name} (ID: {user.id})")
    try:
        response = requests.get("https://bitpay.com/api/rates/BTC/USD")
        price_data = response.json()
        btc_price = price_data['rate']
        await update.message.reply_text(f"The current price of Bitcoin is ${btc_price:.2f}.")
    except Exception as e:
        logger.error(f"Error fetching Bitcoin price: {e}")
        await update.message.reply_text("Sorry, I couldn't fetch the Bitcoin price at the moment.")

# Define the /fee command handler
async def fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the recommended transaction fees in sats/vB."""
    user = update.effective_user
    logger.info(f"Received /fee command from {user.full_name} (ID: {user.id})")
    try:
        response = requests.get("https://bitpay.com/api/rates/BTC/USD")
        price_data = response.json()
        btc_price = price_data['rate']
        
        # Calculate the fee cost in USD based on an average transaction size of 140 vbytes
        def calculate_fee_cost(fee_rate):
            return (fee_rate * 140 * 0.00000001 * btc_price)

        fee_message = (
            f"No Priority: {minimum_fee} sat/vB (${calculate_fee_cost(minimum_fee):.2f})\n"
            f"Low Priority: {economy_fee} sat/vB (${calculate_fee_cost(economy_fee):.2f})\n"
            f"Medium Priority: {hour_fee} sat/vB (${calculate_fee_cost(hour_fee):.2f})\n"
            f"High Priority: {half_hour_fee} sat/vB (${calculate_fee_cost(half_hour_fee):.2f})\n"
            f"Fastest: {fastest_fee} sat/vB (${calculate_fee_cost(fastest_fee):.2f})\n"
        )
        await update.message.reply_text(fee_message)
    except Exception as e:
        logger.error(f"Error fetching transaction fees: {e}")
        await update.message.reply_text("Sorry, I couldn't fetch the transaction fees at the moment.")

# Define a sample restricted command handler
async def restricted_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A restricted command that only allowed users can access."""
    user = update.effective_user
    logger.info(f"Received /restricted command from {user.full_name} (ID: {user.id})")
    if not is_user_allowed(user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    await update.message.reply_text("This is a restricted command.")

# Define the main function to start the bot
async def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).job_queue(JobQueue()).build()

    # Set bot commands
    commands = [
        BotCommand("price", "Get the current price of Bitcoin in USD"),
        BotCommand("fee", "Get the recommended transaction fees in sats/vB"),
        BotCommand("nextmeetup", "Get the date of the next meetup"),
        BotCommand("guess", "Submit a guess for the Bitcoin price at the next meetup"),
    ]
    
    async def set_commands():
        await application.bot.set_my_commands(commands)

    # Add command handlers
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("fee", fee))
    application.add_handler(CommandHandler("restricted", restricted_command))
    application.add_handler(CommandHandler("nextmeetup", nextmeetup))
    application.add_handler(CommandHandler("guess", guess))

    # Set the commands
    await set_commands()

    # Schedule the announcement
    await schedule_announcement(application)

    # Run the bot until the user presses Ctrl-C
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())