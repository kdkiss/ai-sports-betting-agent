import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, JobQueue
from telegram.error import NetworkError
import tenacity
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.agents.parlay_agent import ParlayAnalysisAgent
from src.agents.matchup_agent import MatchupAnalysisAgent
from src.clients.sports_data_client import SportsDataClient
from src.data.search_client import SearchClient
from src.data.weather_client import WeatherClient

logger = logging.getLogger(__name__)

# Patch JobQueue to use a scheduler with pytz.UTC
original_jobqueue_init = JobQueue.__init__

def patched_jobqueue_init(self, *args, **kwargs):
    original_jobqueue_init(self, *args, **kwargs)
    self.scheduler = AsyncIOScheduler(timezone=pytz.UTC)

JobQueue.__init__ = patched_jobqueue_init

class TelegramBot:
    """Telegram bot for sports betting analysis."""

    def __init__(self, token, llm, sports_data_client, search_client, weather_client=None, custom_sync_client=None, custom_async_client=None):
        """Initialize the bot with dependencies."""
        # Create the Application using the builder (the patched JobQueue will be used)
        self.application = Application.builder().token(token).build()

        self.llm = llm
        self.sports_data_client = sports_data_client
        self.search_client = search_client
        self.weather_client = weather_client
        self.custom_sync_client = custom_sync_client
        self.custom_async_client = custom_async_client

        # Initialize agents
        self.parlay_agent = ParlayAnalysisAgent(self.llm, self.search_client, self.sports_data_client)
        self.matchup_agent = MatchupAnalysisAgent(self.llm, self.sports_data_client, self.weather_client, self.search_client)

        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_image))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def start(self, update, context):
        """Handle the /start command."""
        await update.message.reply_text("Welcome to the Sports Betting Bot! Upload a betting slip image or send a matchup (e.g., 'Team A - Team B') to analyze.")

    async def handle_image(self, update, context):
        """Handle image uploads (betting slips)."""
        try:
            photo = update.message.photo[-1]
            file = await photo.get_file()
            image_bytes = await file.download_as_bytearray()

            # Perform OCR to extract text
            text = self.perform_ocr(image_bytes)
            logger.debug(f"OCR output: {text}")

            # Analyze the parlay
            analysis = await self.parlay_agent.analyze({"text": text})
            if "error" in analysis:
                await update.message.reply_text(f"Error analyzing parlay: {analysis['error']}")
                return

            # Format the response
            response = self.format_parlay_analysis(analysis)
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            await update.message.reply_text("Sorry, something went wrong while processing your request. The error has been logged and will be investigated.")

    async def handle_text(self, update, context):
        """Handle text messages (matchup analysis)."""
        try:
            text = update.message.text
            teams = self.extract_teams_from_text(text)
            if len(teams) < 2:
                await update.message.reply_text("Please provide a matchup in the format 'Team A - Team B'.")
                return

            # Analyze the matchup
            analysis = await self.matchup_agent.analyze({
                "text": text,
                "team1": {"name": teams[0]},
                "team2": {"name": teams[1]}
            })
            if "error" in analysis:
                await update.message.reply_text(f"Error analyzing matchup: {analysis['error']}")
                return

            # Format the response
            response = self.format_matchup_analysis(analysis)
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Error processing text: {e}", exc_info=True)
            await update.message.reply_text("Sorry, something went wrong while processing your request. The error has been logged and will be investigated.")

    def perform_ocr(self, image_bytes):
        """Perform OCR on the image (placeholder)."""
        # Replace with actual OCR implementation
        return ""

    def extract_teams_from_text(self, text):
        """Extract team names from text."""
        import re
        match = re.match(r"^(.*?)\s*-\s*(.*?)$", text.strip())
        if match:
            return [match.group(1).strip(), match.group(2).strip()]
        return []

    def format_parlay_analysis(self, analysis):
        """Format parlay analysis for display."""
        if "error" in analysis:
            return f"Error: {analysis['error']}"

        overall = analysis['overall_rating']
        anal = analysis['analysis']
        rec = analysis['recommendations']
        bankroll = analysis['bankroll_advice']

        return (
            "PARLAY ANALYSIS:\n"
            "- OVERALL RATING:\n"
            f"  - CONFIDENCE: {overall['confidence']}/10\n"
            f"  - RISK LEVEL: {overall['risk_level']}\n"
            f"  - EXPECTED VALUE: {overall['expected_value']}\n\n"
            "- ANALYSIS:\n"
            f"  - STRENGTHS: {', '.join(anal['strengths'])}\n"
            f"  - CONCERNS: {', '.join(anal['concerns'])}\n\n"
            "- RECOMMENDATIONS:\n"
            f"  - PRIMARY: {rec['primary']}\n"
            f"  - ALTERNATIVES: {', '.join(rec['alternatives'])}\n\n"
            "- BANKROLL ADVICE:\n"
            f"  - RECOMMENDED STAKE: {bankroll['recommended_stake']}\n"
            f"  - MAX RISK: {bankroll['max_risk']}"
        )

    def format_matchup_analysis(self, analysis):
        """Format matchup analysis for display."""
        if "error" in analysis:
            return f"Error: {analysis['error']}"

        pred = analysis['prediction']
        factors = analysis['key_factors']
        risk = analysis['risk_assessment']
        betting = analysis['betting_recommendations']
        insights = analysis['insights']

        return (
            "MATCHUP ANALYSIS:\n"
            f"- WINNER: {pred['winner']}\n"
            f"- CONFIDENCE: {pred['confidence']}/10\n"
            f"- SCORE RANGE: {pred['score_range']}\n\n"
            "KEY FACTORS:\n" +
            "\n".join(f"- {factor}" for factor in factors) + "\n\n"
            f"RISK ASSESSMENT: {risk}\n\n"
            "BETTING RECOMMENDATIONS:\n"
            f"- MONEYLINE: {betting['moneyline']}\n"
            f"- SPREAD: {betting['spread']}\n"
            f"- TOTALS: {betting['totals']}\n\n"
            "INSIGHTS:\n" +
            "\n".join(f"- {insight}" for insight in insights)
        )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type(NetworkError),
        before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
        reraise=True
    )
    async def run_with_retry(self):
        """Run the bot with retry logic for network errors."""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(
            drop_pending_updates=True,
            poll_interval=1.0,
            timeout=10,
            bootstrap_retries=3
        )
        logger.info("Bot started successfully")
        print("Bot is now running and waiting for messages on Telegram (@daleleleelel_bot). Press Ctrl+C to stop.")

    async def stop(self):
        """Stop the bot and clean up resources."""
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        # Clean up HTTP clients
        if self.custom_sync_client:
            self.custom_sync_client.close()
        if self.custom_async_client:
            await self.custom_async_client.aclose()
        logger.info("Bot stopped and resources cleaned up")

    def run(self):
        """Run the bot."""
        try:
            asyncio.run(self.run_with_retry())
        except KeyboardInterrupt:
            asyncio.run(self.stop())
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Failed to start bot: {e}", exc_info=True)
            asyncio.run(self.stop())
            raise