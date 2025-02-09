import logging
import requests
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
import nest_asyncio

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

# Define the /price command handler
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the current price of Bitcoin in USD."""
    try:
        response = requests.get("https://bitpay.com/api/rates/BTC/USD")
        data = response.json()
        price = data['rate']
        await update.message.reply_text(f"The current price of Bitcoin is ${price:.2f} USD.")
    except Exception as e:
        logger.error(f"Error fetching Bitcoin price: {e}")
        await update.message.reply_text("Sorry, I couldn't fetch the Bitcoin price at the moment.")

# Define the /fee command handler
async def fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the recommended transaction fees in sats/vB and their cost in USD."""
    try:
        # Fetch the recommended fees
        response = requests.get("https://mempool.space/api/v1/fees/recommended")
        fee_data = response.json()
        fastest_fee = fee_data['fastestFee']
        half_hour_fee = fee_data['halfHourFee']
        hour_fee = fee_data['hourFee']
        economy_fee = fee_data['economyFee']
        minimum_fee = fee_data['minimumFee']
        
        # Fetch the current Bitcoin price
        response = requests.get("https://bitpay.com/api/rates/BTC/USD")
        price_data = response.json()
        btc_price = price_data['rate']
        
        # Calculate the fee cost in USD based on an average transaction size of 140 vbytes
        def calculate_fee_cost(fee_rate):
            return (fee_rate * 140 * 0.00000001 * btc_price)

        fee_message = (
            f"No Priority: {minimum_fee} sat/vB (${calculate_fee_cost(minimum_fee):.2f})\n"
            f"Low Priority: {economy_fee} sat/vB (${calculate_fee_cost(economy_fee):.2f})\n"
            f"Medium Priority: {hour_fee} sat/vB (${calculate_fee_cost(hour_fee)::.2f})\n"
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
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    await update.message.reply_text("This is a restricted command.")

async def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Set bot commands
    commands = [
        BotCommand("price", "Get the current price of Bitcoin in USD"),
        BotCommand("fee", "Get the recommended transaction fees in sats/vB")
    ]
    
    async def set_commands():
        await application.bot.set_my_commands(commands)

    # Add command handlers
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("fee", fee))
    application.add_handler(CommandHandler("restricted", restricted_command))

    # Set the commands
    await set_commands()

    # Run the bot until the user presses Ctrl-C
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
