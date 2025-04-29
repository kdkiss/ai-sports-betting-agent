import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.agents.parlay_agent import ParlayAnalysisAgent
from src.agents.matchup_agent import MatchupAnalysisAgent
from src.agents.value_agent import ValueBettingAgent
from src.agents.bankroll_agent import BankrollManagementAgent
from src.services.llm_service import GroqLLM  # Changed from DeepSeekLLM
from src.bot.telegram_bot import TelegramBot

# Force stdout to flush immediately
sys.stdout.reconfigure(line_buffering=True)

def main():
    """Initialize and start the sports betting assistant."""
    print("\n=== Sports Betting Assistant Starting ===")
    
    # Load environment variables
    load_dotenv()
    print("✓ Environment variables loaded")
    
    # Initialize shared LLM instance
    print("Initializing LLM service...")
    llm = GroqLLM()  # Changed from DeepSeekLLM
    print("✓ LLM service initialized")
    
    # Initialize agents
    print("Initializing agents...")
    agents = {
        'parlay': ParlayAnalysisAgent(llm),
        'matchup': MatchupAnalysisAgent(llm),
        'value': ValueBettingAgent(llm),
        'bankroll': BankrollManagementAgent(llm)
    }
    print("✓ All agents initialized")
    
    # Initialize and run Telegram bot
    print("\nStarting Telegram bot...")
    bot = TelegramBot(
        token=os.getenv('TELEGRAM_BOT_TOKEN'),
        agents=agents
    )
    print("✓ Bot instance created")
    
    print("\nStarting bot polling...")
    bot.run()

if __name__ == '__main__':
    main()