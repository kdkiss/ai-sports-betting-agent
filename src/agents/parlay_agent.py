import logging
from typing import Dict
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
                return "Please send your bet details as a photo or text."
                
            # Analyze the text
            analysis = await self.bet_analyzer.analyze_text(text)
            
            # Format the response
            return self._format_response(analysis)
            
        except Exception as e:
            logger.error(f"Error in parlay analysis: {str(e)}")
            return "Sorry, something went wrong. Please try again or send the bet details as text."
            
    def _format_response(self, analysis: Dict) -> str:
        """Format the analysis into a readable response."""
        
        # Start with overall assessment
        response = [
            "🎯 *BET SLIP ANALYSIS*\n",
            f"*Overall Risk Level:* {'🔴 High' if analysis['overall_risk'] == 'High' else '🟡 Medium' if analysis['overall_risk'] == 'Medium' else '🟢 Low'}\n"
        ]
        
        # Add individual leg analysis
        response.append("\n*Individual Legs:*")
        
        for leg in analysis['legs']:
            status = "⚠️ RISKY" if leg['is_risky'] else "✅ SAFE" if leg['is_safe'] else "📍 NEUTRAL"
            
            response.append(f"\n{status} | {leg['player']} - {leg['bet_type']}")
            response.append(f"Line: {leg['line']}+ @ {leg['odds']}")
            
            if leg['risk_factors']:
                response.append("Risk Factors:")
                for factor in leg['risk_factors']:
                    response.append(f"• {factor}")
                    
            if leg['safety_factors']:
                response.append("Safety Factors:")
                for factor in leg['safety_factors']:
                    response.append(f"• {factor}")
                    
        # Add recommendations based on overall risk
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