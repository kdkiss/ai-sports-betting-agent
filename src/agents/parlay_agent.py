import logging
import re
from typing import Dict, List
from ..services.bet_analyzer import BetAnalyzer

logger = logging.getLogger(__name__)

class ParlayAnalysisAgent:
    def __init__(self, llm=None):
        self.bet_analyzer = BetAnalyzer(llm)
        
    async def analyze(self, data: Dict) -> str:
        """Analyze parlay bet data and return formatted analysis."""
        try:
            # Get text from data
            text = data.get('text', '')
            if not text:
                logger.warning("No text provided in input data")
                return "Please send your bet details as a photo or text."
                
            # Preprocess and parse the text
            parsed_bets = self._parse_ocr_text(text)
            if not parsed_bets:
                logger.error("No valid bets parsed from text")
                return (
                    "Sorry, I couldn't read any valid bets from the image. "
                    "The text appears unclear or doesn't contain recognizable bet details. "
                    "Please try a higher-resolution image, ensure text is legible, or send the bet details as text "
                    "(e.g., 'Lakers ML +150 Wager: $100')."
                )
                
            # Format parsed bets for BetAnalyzer
            cleaned_text = self._format_bets_for_analyzer(parsed_bets)
            logger.info(f"Parsed bets: {cleaned_text}")
            
            # Analyze the text
            analysis = await self.bet_analyzer.analyze_text(cleaned_text)
            
            # Format the response
            return self._format_response(analysis)
            
        except Exception as e:
            logger.error(f"Error in parlay analysis: {str(e)}", exc_info=True)
            return (
                "Sorry, something went wrong while analyzing your bet slip. "
                "Please try again with a clearer image or send the bet details as text."
            )
            
    def _parse_ocr_text(self, text: str) -> List[Dict]:
        """Parse noisy OCR text into structured bet data."""
        bets = []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        for line in lines:
            # Match team/player name, bet type (ML, spread, total), odds, and optional wager
            bet_match = re.match(
                r'([\w\s]+?)?\s*(ML|[\+\-]\d+\.\d|O/U\s*\d+\.\d)?\s*([\+\-]\d+|\d+[\+\-])\s*(\$?\d+\$?)?',
                line,
                re.IGNORECASE
            )
            if bet_match:
                player_team = bet_match.group(1).strip() if bet_match.group(1) else 'Unknown'
                bet_type = bet_match.group(2) or 'ML'
                if bet_type.startswith('O/U'):
                    bet_type = f"Total {bet_type}"
                odds = bet_match.group(3)
                # Fix reversed odds (e.g., "258+")
                if odds and odds[-1] in ['+', '-']:
                    odds = odds[-1] + odds[:-1]
                wager = bet_match.group(4) or 'N/A'
                bets.append({
                    'player': player_team,
                    'bet_type': bet_type,
                    'line': bet_type if bet_type != 'ML' else 'N/A',
                    'odds': odds,
                    'wager': wager
                })
            
            # Match wager or payout lines (e.g., "Wager: $100", "To Win: $280")
            wager_match = re.match(r'(Wager|To Win):\s*\$(\d+)', line, re.IGNORECASE)
            if wager_match and bets:
                bets[-1][wager_match.group(1).lower()] = f"${wager_match.group(2)}"
        
        # Clean up noisy text
        for bet in bets:
            # Ensure odds are valid (e.g., "+258")
            if not re.match(r'[\+\-]\d+', bet['odds']):
                cleaned_odds = re.search(r'([\+\-]\d+|\d+[\+\-])', bet['odds'])
                if cleaned_odds:
                    odds = cleaned_odds.group(1)
                    if odds[-1] in ['+', '-']:
                        odds = odds[-1] + odds[:-1]
                    bet['odds'] = odds
            # Clean player name
            bet['player'] = re.sub(r'[^\w\s]', '', bet['player']).strip()
        
        return bets

    def _format_bets_for_analyzer(self, bets: List[Dict]) -> str:
        """Format parsed bets into text for BetAnalyzer."""
        formatted = []
        for bet in bets:
            line = f"{bet['player']} {bet['bet_type']} {bet['odds']}"
            if bet.get('wager') != 'N/A':
                line += f" Wager: {bet['wager']}"
            if bet.get('to win'):
                line += f" To Win: {bet['to win']}"
            formatted.append(line)
        return '\n'.join(formatted)

    def _format_response(self, analysis: Dict) -> str:
        """Format the analysis into a readable response."""
        response = [
            "🎯 *BET SLIP ANALYSIS*\n",
            f"*Overall Risk Level:* {'🔴 High' if analysis['overall_risk'] == 'High' else '🟡 Medium' if analysis['overall_risk'] == 'Medium' else '🟢 Low'}\n"
        ]
        
        response.append("\n*Individual Legs:*")
        
        for leg in analysis['legs']:
            status = "⚠️ RISKY" if leg['is_risky'] else "✅ SAFE" if leg['is_safe'] else "📍 NEUTRAL"
            response.append(f"\n{status} | {leg['player']} - {leg['bet_type']}")
            response.append(f"Line: {leg['line']} @ {leg['odds']}")
            
            if leg['risk_factors']:
                response.append("Risk Factors:")
                for factor in leg['risk_factors']:
                    response.append(f"• {factor}")
                    
            if leg['safety_factors']:
                response.append("Safety Factors:")
                for factor in leg['safety_factors']:
                    response.append(f"• {factor}")
                    
        response.append("\n*Recommendations:*")
        if analysis['overall_risk'] == 'High':
            response.append("• Consider breaking this parlay into smaller bets")
            response.append("• Monitor player news and injury reports closely")
            response.append("• Look for alternative lines with better value")
        elif analysis['overall_risk'] == 'Medium':
            response.append("• Watch for line movements before placing")
            response.append("• Consider key player matchups")
        else:
            response.append("• Lines and odds appear reasonable")
            response.append("• Still monitor pre-game updates")
            
        return "\n".join(response)