# Jersey City Bitcoin Telegram Bot

This is the Jersey City Bitcoin Telegram Bot, a simple bot that provides the current price of Bitcoin in USD and recommended transaction fees in sats/vB. The bot also includes a restricted command that only allowed users can access.

## Features

- Get the current price of Bitcoin in USD.
- Get recommended transaction fees in sats/vB.
- Get the date of the next meetup, which defaults to the second Thursday of the month.
- Restricted command for authorized users.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram user ID(s) from [@userinfobot](https://t.me/userinfobot)

### Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/Jersey-City-Bitcoin/TelegramBot.git
    cd jcbtcbot
    ```

2. Create a virtual environment and activate it:

    ```sh
    python -m venv myenv
    source myenv/bin/activate  # On Windows, use `myenv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

4. Create a [.env](http://_vscodecontentref_/0) file based on the [.env.example](http://_vscodecontentref_/1) file:

    ```sh
    cp .env.example .env
    ```

5. Edit the [.env](http://_vscodecontentref_/2) file to include your bot token and allowed user IDs:

    ```env
    BOT_TOKEN=your_bot_token_here
    ALLOWED_USERS=123456789,987654321
    ```

### Running the Bot

1. Start the bot:

    ```sh
    python jcbtcbot.py
    ```

2. The bot will start and you can interact with it on Telegram.

### Available Commands

- `/price` - Get the current price of Bitcoin in USD.
- `/fee` - Get the recommended transaction fees in sats/vB.
- `/nextmeetup` - Get the date of the next meetup, which defaults to the second Thursday of the month.
- `/restricted` - A restricted command that only allowed users can access.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.