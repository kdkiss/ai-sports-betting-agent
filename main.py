import os
import logging
from src.bot.telegram_bot import TelegramBot
from src.clients.sports_data_client import SportsDataClient
from src.data.search_client import SearchClient
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()

# Configure logging to write to both file and console
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler for bot.log
file_handler = logging.FileHandler('bot.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Console handler for terminal output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def main():
    """Main function to initialize and run the bot."""
    try:
        # Load environment variables
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        groq_api_key = os.getenv("GROQ_API_KEY")
        sports_api_key = os.getenv("SPORTS_API_KEY")

        if not all([telegram_token, groq_api_key, sports_api_key]):
            missing = [k for k, v in {
                "TELEGRAM_BOT_TOKEN": telegram_token,
                "GROQ_API_KEY": groq_api_key,
                "SPORTS_API_KEY": sports_api_key
            }.items() if not v]
            logger.error(f"Missing environment variables: {missing}")
            raise ValueError(f"Missing environment variables: {missing}")

        # Initialize custom httpx clients to avoid proxies issue
        custom_sync_client = httpx.Client(
            timeout=30.0,
            follow_redirects=True
        )
        custom_async_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True
        )

        # Initialize LLM with custom clients
        groq_llm = ChatGroq(
            api_key=groq_api_key,
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            temperature=0.7,
            max_tokens=1000,
            client=custom_sync_client,
            async_client=custom_async_client
        )

        # Initialize clients
        sports_data_client = SportsDataClient(api_key=sports_api_key)
        search_client = SearchClient()
        
        # Initialize bot with HTTP clients for cleanup
        bot = TelegramBot(
            token=telegram_token,
            llm=groq_llm,
            sports_data_client=sports_data_client,
            search_client=search_client,
            custom_sync_client=custom_sync_client,
            custom_async_client=custom_async_client
        )

        # Run the bot
        logger.info("Starting the bot...")
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()