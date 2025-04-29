from typing import Dict, Any
from .base_agent import BaseAgent
import json
import re
import logging

logger = logging.getLogger(__name__)

class ValueBettingAgent(BaseAgent):
    """Agent responsible for analyzing value betting opportunities."""

    def __init__(self, llm):
        """Initialize the agent with LLM service."""
        super().__init__(llm=llm)

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a value betting opportunity."""
        try:
            response = await self._get_llm_analysis(context)
            parsed_response = self._parse_response(response)
            return parsed_response
        except Exception as e:
            logger.error(f"Error in value analysis: {e}", exc_info=True)
            return {
                "error": f"Failed to analyze value bet: {str(e)}",
                "value_rating": {"score": 0, "edge": "0%", "confidence": 0},
                "market_analysis": {"true_probability": 0, "implied_probability": 0, "edge": 0, "market_efficiency": "Unknown"},
                "betting_advice": {"recommended_size": "N/A", "timing": "N/A", "max_price": "N/A", "stop_loss": "N/A"},
                "supporting_factors": [],
                "risk_factors": [],
                "action_items": []
            }

    def _create_prompt(self, context: Dict[str, Any]) -> str:
        """Create a prompt for value betting analysis."""
        text = context.get('text', '')
        team1 = context.get('team1', {}).get('name', 'Unknown Team 1')
        team2 = context.get('team2', {}).get('name', 'Unknown Team 2')
        matchup_context = context.get('matchup_context', {})

        return f"""You are an expert sports betting analyst. Analyze the value betting opportunity and return the response in valid JSON format, enclosed in ```json\n...\n```. Do not include any additional text outside the JSON block. The JSON must follow this structure:

```json
{{
  "value_rating": {{
    "score": 7,
    "edge": "10%",
    "confidence": 7
  }},
  "market_analysis": {{
    "true_probability": 50,
    "implied_probability": 45,
    "edge": 5,
    "market_efficiency": "Low"
  }},
  "betting_advice": {{
    "recommended_size": "$100",
    "timing": "Now",
    "max_price": "2.00",
    "stop_loss": "1.80"
  }},
  "supporting_factors": ["Factor 1"],
  "risk_factors": ["Risk 1"],
  "action_items": ["Action 1"]
}}
```

Betting Details:
- Teams: {team1} vs {team2}
- Text: {text}
- Matchup Context: {matchup_context}

Consider:
1. Implied probabilities
2. Market inefficiencies
3. Risk-reward balance
4. Team performance

Return only the JSON response in the specified format, enclosed in ```json\n...\n```."""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured value analysis."""
        logger.debug(f"Raw LLM response: {response}")
        try:
            json_match = re.search(r'```json\n([\s\S]*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}", exc_info=True)
            return {
                "error": "Failed to parse LLM response as JSON",
                "value_rating": {"score": 0, "edge": "0%", "confidence": 0},
                "market_analysis": {"true_probability": 0, "implied_probability": 0, "edge": 0, "market_efficiency": "Unknown"},
                "betting_advice": {"recommended_size": "N/A", "timing": "N/A", "max_price": "N/A", "stop_loss": "N/A"},
                "supporting_factors": [],
                "risk_factors": [],
                "action_items": []
            }