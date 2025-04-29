import logging
import traceback
from pathlib import Path
from typing import Optional, List, Dict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ..agents.parlay_agent import ParlayAnalysisAgent
from ..agents.matchup_agent import MatchupAnalysisAgent
from ..agents.value_agent import ValueBettingAgent
from ..agents.bankroll_agent import BankrollManagementAgent
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import os
import sys

# Configure logger
logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot for sports betting analysis."""

    def __init__(self, token: str, agents: dict):
        """Initialize the bot with a token and agent instances."""
        print("\n=== Bot Initializing ===")
        
        self.token = token
        self.parlay_agent = agents['parlay']
        self.matchup_agent = agents['matchup']
        self.value_agent = agents['value']
        self.bankroll_agent = agents['bankroll']
        self.application = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        
        print("Configuring message handlers...")
        
        # Verify Tesseract installation
        try:
            tesseract_version = pytesseract.get_tesseract_version()
            print(f"✓ Tesseract version: {tesseract_version}")
        except Exception as e:
            print("✗ Error verifying Tesseract:", str(e))
            raise RuntimeError("Failed to verify Tesseract installation")

    async def _log_received(self, update: Update, message_type: str):
        """Simple console log for received messages."""
        print("\n" + "="*50)
        print(f"📨 MESSAGE RECEIVED: {message_type}")
        print(f"👤 From: {update.message.from_user.username or 'Unknown'}")
        if update.message.text:
            print(f"💬 Text: {update.message.text[:50]}...")
        if update.message.photo:
            print("📸 Contains: Photo")
        if update.message.document:
            print("📎 Contains: Document")
        if update.message.caption:
            print(f"📝 Caption: {update.message.caption}")
        print("="*50 + "\n")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        print("\n" + "="*50)
        print("🚀 START COMMAND RECEIVED")
        print(f"From: {update.message.from_user.username}")
        print("="*50)
        
        await self._log_received(update, "COMMAND: /start")
        await self._log_message(update, "Command: /start")
        welcome_message = """🎯 Welcome to the Sports Betting Assistant! 

I can help you analyze:
• Single or multiple parlay bets
• Team matchups
• Value betting opportunities
• Bankroll management

Just send me what you'd like to analyze. For example:
• Send multiple parlays separated by blank lines:
Parlay 1:
Lakers ML, Celtics -5.5
$100 to win $280

Parlay 2:
Warriors -4, Suns ML
$150 to win $390

• Or just paste your bet slips and I'll figure it out!
• You can also ask "Compare these parlays" or "Which is the best bet?"

You can also use commands:
/analyze - Analyze any bet or parlay
/help - Show this help message
"""
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        print("\n" + "="*50)
        print("❓ HELP COMMAND RECEIVED")
        print(f"From: {update.message.from_user.username}")
        print("="*50)
        
        await self._log_received(update, "COMMAND: /help")
        await self._log_message(update, "Command: /help")
        await self.start(update, context)

    async def analyze_parlay_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /analyze command."""
        print("\n" + "="*50)
        print("🔍 ANALYZE COMMAND RECEIVED")
        print(f"From: {update.message.from_user.username}")
        if update.message.text:
            print(f"Text: {update.message.text}")
        print("="*50)
        await self._log_received(update, "COMMAND: /analyze")
        await self._log_message(update, "Command: /analyze")
        # ... rest of analyze_parlay_command code ...

    def _split_parlays(self, text: str) -> List[str]:
        """Split text into individual parlays based on common patterns."""
        parlays = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if len(parlays) == 1:
            import re
            parlays = [p.strip() for p in re.split(r'(?i)(?:^|\n)(?:parlay|ticket)\s*(?:\d+|\w+)?:', text) if p.strip()]
            
        if len(parlays) == 1:
            return [text]
            
        return parlays

    async def _log_message(self, update: Update, message_type: str):
        """Log incoming message details to console."""
        print("\n=== Incoming Message ===")
        print(f"Type: {message_type}")
        print(f"From: {update.message.from_user.username or 'Unknown'}")
        print(f"Chat Type: {update.message.chat.type}")
        print(f"Message ID: {update.message.message_id}")
        
        if update.message.photo:
            print("Contains: Photo")
            print(f"Number of sizes: {len(update.message.photo)}")
            print(f"Largest size: {update.message.photo[-1].width}x{update.message.photo[-1].height}")
        
        if update.message.document:
            print("Contains: Document")
            print(f"Filename: {update.message.document.file_name}")
            print(f"MIME type: {update.message.document.mime_type}")
        
        if update.message.text:
            print("Contains: Text")
            print(f"Text: {update.message.text[:100]}...")
        
        if update.message.caption:
            print("Contains: Caption")
            print(f"Caption: {update.message.caption}")
        
        print("========================\n")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        print("\n!!!!! TEXT MESSAGE RECEIVED !!!!!")
        print(f"MESSAGE: {update.message.text}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        
        try:
            text = update.message.text
            
            if any(word in text.lower() for word in ['parlay', 'ticket', 'slip']) and len(text.split('\n')) > 2:
                parlays = self._split_parlays(text)
                if len(parlays) > 1:
                    await self._analyze_multiple_parlays(update, parlays)
                    return

            if any(word in text.lower() for word in ['parlay', 'ticket', 'slip', 'multi']):
                analysis = await self.parlay_agent.analyze({'text': text})
                await self._format_parlay_response(update, analysis)
            
            elif 'vs' in text or any(word in text.lower() for word in ['matchup', 'game', 'match', 'playing']):
                analysis = await self.matchup_agent.analyze({'text': text})
                await self._format_matchup_response(update, analysis)
            
            elif any(word in text.lower() for word in ['value', 'odds', 'price', 'line']):
                analysis = await self.value_agent.analyze({'text': text})
                await self._format_value_response(update, analysis)
            
            elif any(word in text.lower() for word in ['bankroll', 'stake', 'bet size', 'units']):
                analysis = await self.bankroll_agent.analyze({'text': text})
                await self._format_bankroll_response(update, analysis)
            
            else:
                await self._analyze_comprehensive(update, text)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text(
                "I encountered an error analyzing your request. Could you try rephrasing it?"
            )

    async def _analyze_multiple_parlays(self, update: Update, parlays: List[str]):
        """Analyze multiple parlays and provide comparative analysis."""
        try:
            analyses = []
            for i, parlay in enumerate(parlays, 1):
                analysis = await self.parlay_agent.analyze({'text': parlay})
                analyses.append(analysis)

            correlations = self._calculate_parlay_correlations(analyses)
            risk_metrics = self._calculate_risk_metrics(analyses)
            portfolio = self._calculate_portfolio_allocation(analyses, correlations, risk_metrics)

            sorted_analyses = sorted(
                enumerate(analyses, 1),
                key=lambda x: (
                    float(x[1]['overall_rating']['expected_value'].strip('%')) * 0.7 +
                    float(risk_metrics[x[0]-1]['sharpe_ratio']) * 0.3
                ),
                reverse=True
            )

            response = """📊 *Comparative Parlay Analysis*

*Rankings (EV & Risk-Adjusted):*
"""
            for i, (idx, analysis) in enumerate(sorted_analyses, 1):
                response += f"#{i}. Parlay {idx} ({analysis['overall_rating']['expected_value']} EV, {risk_metrics[idx-1]['sharpe_ratio']:.2f} Sharpe)\n"

            response += "\n*Detailed Analysis:*\n"
            for i, parlay_analysis in enumerate(analyses, 1):
                response += f"""
*Parlay {i}:*
• Rating: {parlay_analysis['overall_rating']['confidence']}/10
• Risk: {parlay_analysis['overall_rating']['risk_level']}
• EV: {parlay_analysis['overall_rating']['expected_value']}
• Sharpe: {risk_metrics[i-1]['sharpe_ratio']:.2f}
• Kelly: {risk_metrics[i-1]['kelly_fraction']:.2%}
• Key Strength: {parlay_analysis['analysis']['strengths'][0]}
• Main Concern: {parlay_analysis['analysis']['concerns'][0]}
"""

            if len(analyses) > 1:
                response += "\n*Correlation Analysis:*\n"
                high_corr_pairs = [
                    (i, j) for i in range(len(analyses)) for j in range(i+1, len(analyses))
                    if correlations[i][j] > 0.5
                ]
                if high_corr_pairs:
                    response += "⚠️ High correlation detected between:\n"
                    for i, j in high_corr_pairs:
                        response += f"• Parlay {i+1} & Parlay {j+1} ({correlations[i][j]:.2%})\n"
                else:
                    response += "✅ No concerning correlations between parlays\n"

            response += "\n*Portfolio Recommendation:*\n"
            response += "Optimal Allocation (Kelly-adjusted):\n"
            for i, alloc in enumerate(portfolio['allocations'], 1):
                if alloc > 0:
                    response += f"• Parlay {i}: {alloc:.1%} of bankroll"
                    if portfolio['hedges'].get(i):
                        response += f" (Hedge: {portfolio['hedges'][i]})\n"
                    else:
                        response += "\n"

            response += f"""
*Portfolio Metrics:*
• Expected Return: {portfolio['expected_return']:.1%}
• Portfolio Risk: {portfolio['portfolio_risk']:.1%}
• Sharpe Ratio: {portfolio['sharpe_ratio']:.2f}
• Max Drawdown: {portfolio['max_drawdown']:.1%}
"""

            if portfolio['warnings']:
                response += "\n⚠️ *Risk Warnings:*\n"
                for warning in portfolio['warnings']:
                    response += f"• {warning}\n"

            response += "\n*Strategy Recommendations:*\n"
            for rec in portfolio['recommendations']:
                response += f"• {rec}\n"

            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in multiple parlay analysis: {e}")
            await update.message.reply_text(
                "I had trouble analyzing multiple parlays. Could you check the format and try again?"
            )

    def _calculate_parlay_correlations(self, analyses: List[dict]) -> List[List[float]]:
        """Calculate correlation matrix between parlays."""
        n = len(analyses)
        correlations = [[1.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i+1, n):
                correlation = 0.0
                teams_i = set(self._extract_teams(analyses[i]))
                teams_j = set(self._extract_teams(analyses[j]))
                if teams_i.intersection(teams_j):
                    correlation += 0.3
                leagues_i = set(self._extract_leagues(analyses[i]))
                leagues_j = set(self._extract_leagues(analyses[j]))
                if leagues_i.intersection(leagues_j):
                    correlation += 0.2
                bet_types_i = set(self._extract_bet_types(analyses[i]))
                bet_types_j = set(self._extract_bet_types(analyses[j]))
                if bet_types_i.intersection(bet_types_j):
                    correlation += 0.1
                correlations[i][j] = correlations[j][i] = min(correlation, 1.0)
        
        return correlations

    def _calculate_risk_metrics(self, analyses: List[dict]) -> List[dict]:
        """Calculate risk-adjusted metrics for each parlay."""
        metrics = []
        
        for analysis in analyses:
            ev = float(analysis['overall_rating']['expected_value'].strip('%')) / 100
            confidence = float(analysis['overall_rating']['confidence']) / 10
            risk_map = {'Low': 0.5, 'Medium': 1.0, 'High': 2.0}
            risk = risk_map[analysis['overall_rating']['risk_level']]
            sharpe_ratio = (ev / risk) if risk > 0 else 0
            kelly_fraction = (ev * confidence) / risk if risk > 0 else 0
            
            metrics.append({
                'sharpe_ratio': sharpe_ratio,
                'kelly_fraction': kelly_fraction,
                'risk_score': risk,
                'expected_value': ev
            })
        
        return metrics

    def _calculate_portfolio_allocation(
        self, 
        analyses: List[dict], 
        correlations: List[List[float]], 
        risk_metrics: List[dict]
    ) -> dict:
        """Calculate optimal portfolio allocation using Kelly Criterion and MPT."""
        n = len(analyses)
        kelly_allocations = [max(0, m['kelly_fraction']) for m in risk_metrics]
        total_kelly = sum(kelly_allocations)
        
        if total_kelly > 0:
            allocations = [k/total_kelly for k in kelly_allocations]
        else:
            allocations = [1/n] * n if n > 0 else []

        for i in range(n):
            for j in range(n):
                if i != j and correlations[i][j] > 0.5:
                    allocations[i] *= (1 - correlations[i][j] * 0.5)
                    allocations[j] *= (1 - correlations[i][j] * 0.5)

        total = sum(allocations)
        if total > 0:
            allocations = [a/total for a in allocations]

        exp_return = sum(a * m['expected_value'] for a, m in zip(allocations, risk_metrics))
        portfolio_risk = sum(sum(
            allocations[i] * allocations[j] * correlations[i][j] * 
            risk_metrics[i]['risk_score'] * risk_metrics[j]['risk_score']
            for j in range(n)
        ) for i in range(n)) ** 0.5
        
        sharpe = exp_return / portfolio_risk if portfolio_risk > 0 else 0
        
        warnings = []
        if portfolio_risk > 0.2:
            warnings.append("High portfolio risk - consider reducing position sizes")
        if any(a > 0.3 for a in allocations):
            warnings.append("Large position sizes detected - consider spreading risk")
        if any(correlations[i][j] > 0.7 for i in range(n) for j in range(i+1, n)):
            warnings.append("Very high correlations - portfolio may be less diversified than it appears")

        recommendations = []
        if portfolio_risk > 0.15:
            recommendations.append("Consider hedging highest risk positions")
        if exp_return < 0.05:
            recommendations.append("Low expected return - may want to wait for better opportunities")
        if sharpe < 1:
            recommendations.append("Poor risk-adjusted return - consider alternative bets")

        hedges = {}
        for i in range(n):
            if risk_metrics[i]['risk_score'] > 1.5 and allocations[i] > 0.1:
                hedges[i+1] = "Consider opposite side at key numbers"

        return {
            'allocations': allocations,
            'expected_return': exp_return,
            'portfolio_risk': portfolio_risk,
            'sharpe_ratio': sharpe,
            'max_drawdown': portfolio_risk * 2.33,
            'warnings': warnings,
            'recommendations': recommendations,
            'hedges': hedges
        }

    def _extract_teams(self, analysis: dict) -> List[str]:
        """Extract team names from analysis."""
        return []

    def _extract_leagues(self, analysis: dict) -> List[str]:
        """Extract league names from analysis."""
        return []

    def _extract_bet_types(self, analysis: dict) -> List[str]:
        """Extract bet types from analysis."""
        return []

    async def _analyze_comprehensive(self, update: Update, text: str):
        """Perform a comprehensive analysis using multiple agents."""
        try:
            matchup_analysis = await self.matchup_agent.analyze({'text': text})
            value_analysis = await self.value_agent.analyze({
                'text': text,
                'matchup_context': matchup_analysis
            })
            bankroll_analysis = await self.bankroll_agent.analyze({
                'text': text,
                'matchup_context': matchup_analysis,
                'value_context': value_analysis
            })
            
            response = f"""📊 *Comprehensive Betting Analysis*

*Game Analysis:*
• Prediction: {matchup_analysis['prediction']['winner']}
• Confidence: {matchup_analysis['prediction']['confidence']}/10
• Key Insight: {matchup_analysis['key_factors'][0]}

*Value Assessment:*
• Edge: {value_analysis['value_rating']['edge']}
• Market Efficiency: {value_analysis['market_analysis']['market_efficiency']}
• Best Bet: {value_analysis['betting_advice']['timing']}

*Bankroll Advice:*
• Recommended Stake: {bankroll_analysis['bet_sizing']['recommended_amount']}
• Risk Level: {bankroll_analysis['risk_management']['risk_of_ruin']}
• Position Size: {bankroll_analysis['bet_sizing']['recommended_units']} units

*Action Items:*
"""
            for item in bankroll_analysis['action_items']:
                response += f"• {item}\n"
            
            response += "\n*Key Risks:*\n"
            for risk in value_analysis['risk_factors']:
                response += f"• {risk}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            await update.message.reply_text(
                "I had trouble with the comprehensive analysis. Could you be more specific about what you'd like to know?"
            )

    async def _format_parlay_response(self, update: Update, analysis: dict):
        """Format and send parlay analysis response."""
        response = f"""📊 *Parlay Analysis*

*Overall Rating:* {analysis['overall_rating']['confidence']}/10
*Risk Level:* {analysis['overall_rating']['risk_level']}
*Expected Value:* {analysis['overall_rating']['expected_value']}

*Strengths:*
"""
        for s in analysis['analysis']['strengths']:
            response += f"• {s}\n"
        
        response += "\n*Concerns:*\n"
        for c in analysis['analysis']['concerns']:
            response += f"• {c}\n"
        
        response += f"""
*Recommendation:* {analysis['recommendations']['primary']}

*Alternative Strategies:*
"""
        for a in analysis['recommendations']['alternatives']:
            response += f"• {a}\n"
        
        response += f"""
*Bankroll Management:*
• Recommended Stake: {analysis['bankroll_advice']['recommended_stake']}
• Maximum Risk: {analysis['bankroll_advice']['max_risk']}
"""
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _format_matchup_response(self, update: Update, analysis: dict):
        """Format and send matchup analysis response."""
        response = f"""🏆 *Matchup Analysis*

*Prediction:*
• Winner: {analysis['prediction']['winner']}
• Confidence: {analysis['prediction']['confidence']}/10
• Score Range: {analysis['prediction']['score_range']}

*Key Factors:*
"""
        for f in analysis['key_factors']:
            response += f"• {f}\n"
        
        response += f"""
*Risk Assessment:* {analysis['risk_assessment']}

*Betting Recommendations:*
• Moneyline: {analysis['betting_recommendations']['moneyline']}
• Spread: {analysis['betting_recommendations']['spread']}
• Totals: {analysis['betting_recommendations']['totals']}

*Key Insights:*
"""
        for i in analysis['insights']:
            response += f"• {i}\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _format_value_response(self, update: Update, analysis: dict):
        """Format and send value analysis response."""
        response = f"""💰 *Value Analysis*

*Rating:* {analysis['value_rating']['score']}/10
*Edge:* {analysis['value_rating']['edge']}
*Confidence:* {analysis['value_rating']['confidence']}

*Market Analysis:*
• True Probability: {analysis['market_analysis']['true_probability']}%
• Implied Probability: {analysis['market_analysis']['implied_probability']}%
• Edge: {analysis['market_analysis']['edge']}%
• Market Status: {analysis['market_analysis']['market_efficiency']}

*Betting Advice:*
• Size: {analysis['betting_advice']['recommended_size']}
• Timing: {analysis['betting_advice']['timing']}
• Max Price: {analysis['betting_advice']['max_price']}
• Stop Loss: {analysis['betting_advice']['stop_loss']}

*Supporting Factors:*
"""
        for f in analysis['supporting_factors']:
            response += f"• {f}\n"
        
        response += "\n*Risk Factors:*\n"
        for r in analysis['risk_factors']:
            response += f"• {r}\n"
        
        response += "\n*Action Items:*\n"
        for i in analysis['action_items']:
            response += f"• {i}\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _format_bankroll_response(self, update: Update, analysis: dict):
        """Format and send bankroll management advice."""
        response = f"""💵 *Bankroll Management Advice*

*Bet Sizing:*
• Recommended Amount: ${analysis['bet_sizing']['recommended_amount']}
• Units: {analysis['bet_sizing']['recommended_units']}
• Kelly Fraction: {analysis['bet_sizing']['kelly_fraction']}
• Maximum Bet: ${analysis['bet_sizing']['max_bet']}

*Risk Management:*
• Portfolio Exposure: {analysis['risk_management']['max_portfolio_exposure']}
• Stop Loss: {analysis['risk_management']['stop_loss_level']}
• Hedging Threshold: {analysis['risk_management']['hedging_threshold']}
• Risk of Ruin: {analysis['risk_management']['risk_of_ruin']}

*Portfolio Strategy:*
• High Confidence: {analysis['bankroll_strategy']['current_allocation']['high_confidence']}
• Medium Confidence: {analysis['bankroll_strategy']['current_allocation']['medium_confidence']}
• Speculative: {analysis['bankroll_strategy']['current_allocation']['speculative']}

*Recommendations:*
"""
        for r in analysis['bankroll_strategy']['recommended_changes']:
            response += f"• {r}\n"
        
        response += f"""
*Position Management:*
• Entry: {analysis['position_management']['entry_strategy']}
• Exit: {analysis['position_management']['exit_strategy']}

*Warnings:*
"""
        for w in analysis['warnings']:
            response += f"• {w}\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def _photo_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming photo messages."""
        try:
            print("\n===== PHOTO MESSAGE RECEIVED =====")
            print(f"From: {update.message.from_user.username}")
            print(f"Number of photo sizes: {len(update.message.photo)}")
            
            processing_msg = await update.message.reply_text("📸 Processing your bet slip...")
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            print(f"Got photo file: {photo.file_id}")
            
            photo_bytes = await file.download_as_bytearray()
            debug_dir = "debug_images"
            os.makedirs(debug_dir, exist_ok=True)
            photo_path = os.path.join(debug_dir, f"betslip_{len(os.listdir(debug_dir))}.jpg")
            with open(photo_path, "wb") as f:
                f.write(photo_bytes)
            print(f"Saved image to: {photo_path}")
            
            await processing_msg.edit_text("✅ Photo saved, extracting text...")
            
            if not hasattr(self, 'image_preprocessor'):
                print("Initializing ImagePreprocessor")
                from ..services.image_preprocessor import ImagePreprocessor
                self.image_preprocessor = ImagePreprocessor()
            
            extracted_text = self.image_preprocessor.process_image(photo_bytes)
            print("\n----- EXTRACTED TEXT -----")
            print(extracted_text)
            print("-------------------------\n")
            
            await processing_msg.edit_text("✅ Text extracted, analyzing bets...")
            analysis = await self.parlay_agent.analyze({'text': extracted_text})
            await processing_msg.delete()
            await update.message.reply_text(analysis, parse_mode='Markdown')
            
        except Exception as e:
            print(f"\nError processing photo: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
            await update.message.reply_text(
                "Sorry, something went wrong. Please try again or send the bet details as text."
            )

    def setup(self):
        """Set up the bot with all necessary handlers."""
        print("\n" + "="*50)
        print("🤖 SETTING UP BOT")
        
        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )
        print("✓ Application built")
        
        if self.application.handlers:
            self.application.handlers.clear()
            print("✓ Cleared existing handlers")
        
        print("\nRegistering handlers...")
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_parlay_command))
        print("✓ Added command handlers (/start, /help, /analyze)")
        
        photo_handler = MessageHandler(
            filters.PHOTO | (filters.Document.IMAGE | filters.Document.Category("image/jpeg") | filters.Document.MimeType("image/png")),
            self._photo_handler
        )
        self.application.add_handler(photo_handler)
        print("✓ Added photo/document handler")
        
        text_handler = MessageHandler(
            filters.TEXT & (~filters.COMMAND),
            self.handle_message
        )
        self.application.add_handler(text_handler)
        print("✓ Added text handler")
        
        self.application.add_error_handler(self._error_handler)
        print("✓ Added error handler")
        
        print("\nAll handlers registered successfully")
        print("="*50 + "\n")

    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log errors and send a message to the user."""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
        try:
            if update and update.message:
                await update.message.reply_text(
                    "❌ Sorry, something went wrong while processing your request.\n"
                    "The error has been logged and will be investigated."
                )
        except:
            pass 

    def run(self):
        """Start the bot."""
        print("\n=== Starting Bot ===")
        
        try:
            if not self.application:
                self.setup()
            
            print("\n" + "="*50)
            print("🤖 BOT STARTING")
            print("✓ Handlers configured")
            print("✓ Starting message polling...")
            print("="*50 + "\n")
            
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except Exception as e:
            print("\n❌ Failed to start bot:", str(e))
            raise