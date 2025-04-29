from typing import Dict, Any
import logging
import json
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class MatchupAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing sports matchups, including team and individual sports."""

    def __init__(self, llm):
        """Initialize the agent with LLM service."""
        super().__init__(llm=llm)
        logger.info("MatchupAnalysisAgent initialized")

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a matchup based on input text or structured context."""
        try:
            text = context.get('text', '')
            if not text:
                logger.error("No text provided for analysis")
                raise ValueError("No text provided for analysis")

            # Parse text to extract player/team names (e.g., "Zverev, Alexander vs Cerundolo, Francisco")
            if 'vs' in text.lower():
                parts = text.split('vs', 1)
                entity1 = parts[0].strip()
                entity2 = parts[1].strip()
            else:
                logger.error("Invalid matchup format: 'vs' not found")
                raise ValueError("Invalid matchup format: expected 'Team1 vs Team2' or 'Player1 vs Player2'")

            # Create a simplified context for the prompt
            simplified_context = {
                'team1': {'name': entity1, 'position': 'N/A', 'form': 'N/A', 'venue_status': 'N/A', 'stats': {}, 'recent_results': []},
                'team2': {'name': entity2, 'position': 'N/A', 'form': 'N/A', 'venue_status': 'N/A', 'stats': {}, 'recent_results': []},
                'h2h_history': 'No history provided',
                'weather': 'N/A',
                'injuries': 'N/A',
                'special_circumstances': 'None'
            }

            logger.info(f"Analyzing matchup: {entity1} vs {entity2}")
            prompt = self._create_prompt(simplified_context)
            response = await self._get_llm_analysis(prompt)
            return self._parse_response(response)

        except Exception as e:
            logger.error(f"Error in matchup analysis: {str(e)}")
            raise

    async def _get_llm_analysis(self, prompt: str) -> str:
        """Fetch analysis from the LLM."""
        try:
            response = await self.llm.generate_response(prompt)
            return response
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            raise

    def _create_prompt(self, context: Dict[str, Any]) -> str:
        """Create a detailed prompt for matchup analysis, supporting teams or individual players."""
        entity1 = context['team1']['name']
        entity2 = context['team2']['name']
        
        return f"""Analyze the following sports matchup between {entity1} and {entity2}:

Entity 1: {entity1}
- Ranking/Position: {context['team1'].get('position', 'N/A')}
- Recent Form: {context['team1'].get('form', 'N/A')}
- Venue Status: {context['team1'].get('venue_status', 'N/A')}
- Key Stats: {context['team1'].get('stats', {})}
- Recent Results: {context['team1'].get('recent_results', [])}

Entity 2: {entity2}
- Ranking/Position: {context['team2'].get('position', 'N/A')}
- Recent Form: {context['team2'].get('form', 'N/A')}
- Venue Status: {context['team2'].get('venue_status', 'N/A')}
- Key Stats: {context['team2'].get('stats', {})}
- Recent Results: {context['team2'].get('recent_results', [])}

Head-to-Head History:
{context.get('h2h_history', 'No history available')}

Additional Factors:
- Weather: {context.get('weather', 'N/A')}
- Injuries: {context.get('injuries', 'N/A')}
- Special Circumstances: {context.get('special_circumstances', 'None')}

Analyze this matchup considering:
1. Recent form and momentum
2. Head-to-head history
3. Venue performance (home/away or court surface for individual sports)
4. Key player matchups or tactical styles
5. Statistical trends
6. External factors (weather, injuries, etc.)

Provide a comprehensive analysis in JSON format with the following structure:
```json
{
    "prediction": {
        "winner": "Name of predicted winner",
        "confidence": integer (1-10),
        "score_range": "Predicted score range (e.g., '6-4, 7-5' for tennis, '2-1' for soccer)"
    },
    "key_factors": ["Factor 1", "Factor 2", ...],
    "risk_assessment": "Low/Medium/High risk with reasoning",
    "betting_recommendations": {
        "moneyline": "Recommendation for moneyline bet",
        "spread": "Recommendation for spread or game handicap bet",
        "totals": "Recommendation for over/under or total games/points bet"
    },
    "insights": ["Insight 1", "Insight 2", ...]
}
```
"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured matchup analysis."""
        try:
            # Assume GroqLLM returns a JSON string
            parsed = json.loads(response)
            
            # Validate required keys
            required_keys = ['prediction', 'key_factors', 'risk_assessment', 'betting_recommendations', 'insights']
            if not all(key in parsed for key in required_keys):
                logger.error("Invalid LLM response structure")
                raise ValueError("Invalid LLM response structure")
            
            # Validate nested keys
            if not all(key in parsed['prediction'] for key in ['winner', 'confidence', 'score_range']):
                logger.error("Invalid prediction structure")
                raise ValueError("Invalid prediction structure")
            if not all(key in parsed['betting_recommendations'] for key in ['moneyline', 'spread', 'totals']):
                logger.error("Invalid betting_recommendations structure")
                raise ValueError("Invalid betting_recommendations structure")
            
            return parsed
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            # Fallback to placeholder if parsing fails
            return {
                'prediction': {
                    'winner': context['team1']['name'],
                    'confidence': 7,
                    'score_range': 'N/A'
                },
                'key_factors': ['Form-based prediction', 'Venue advantage'],
                'risk_assessment': 'Medium - Limited data',
                'betting_recommendations': {
                    'moneyline': 'Consider ' + context['team1']['name'],
                    'spread': 'N/A',
                    'totals': 'N/A'
                },
                'insights': ['Based on input text analysis']
            }
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            raise