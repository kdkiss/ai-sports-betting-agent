from typing import Dict, Any
from .base_agent import BaseAgent
import json
import re
import logging

logger = logging.getLogger(__name__)

class MatchupAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing matchups between teams."""

    def __init__(self, llm, sports_data_client, weather_client, search_client):
        """Initialize the agent with LLM service, sports data client, weather client, and search client."""
        super().__init__(llm=llm, sports_data_client=sports_data_client, weather_client=weather_client)
        self.sports_data_client = sports_data_client
        self.weather_client = weather_client
        self.search_client = search_client

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a matchup between two teams."""
        try:
            if 'team1' not in context or 'name' not in context.get('team1', {}):
                logger.error("Invalid context: 'team1' or 'team1.name' missing")
                raise ValueError("Missing team1 name in context")
            if 'team2' not in context or 'name' not in context.get('team2', {}):
                logger.error("Invalid context: 'team2' or 'team2.name' missing")
                raise ValueError("Missing team2 name in context")

            logger.debug(f"Context for matchup analysis: {context}")

            stats = await self.sports_data_client.get_stats('Soccer', context)
            context['stats'] = stats
            logger.debug(f"Fetched stats: {stats}")

            weather = await self.weather_client.get_forecast(context)
            context['weather'] = weather
            logger.debug(f"Fetched weather: {weather}")

            insights = await self.search_client.gather_insights(context)
            if not insights or 'overall_sentiment' not in insights:
                logger.warning("SearchClient returned empty or invalid insights")
            context['insights'] = insights
            logger.debug(f"Fetched insights: {insights}")

            response = await self._get_llm_analysis(context)
            logger.debug(f"Raw LLM response: {response}")

            parsed_response = self._parse_response(response)
            return parsed_response
        except Exception as e:
            logger.error(f"Error in matchup analysis: {e}", exc_info=True)
            return {
                "error": f"Failed to analyze matchup: {str(e)}",
                "prediction": {"winner": "Unknown", "confidence": 0, "score_range": "N/A"},
                "key_factors": [],
                "risk_assessment": "Unknown",
                "betting_recommendations": {"moneyline": "N/A", "spread": "N/A", "totals": "N/A"},
                "insights": []
            }

    def _create_prompt(self, context: Dict[str, Any]) -> str:
        """Create a prompt for matchup analysis."""
        team1 = context.get('team1', {}).get('name', 'Unknown Team 1')
        team2 = context.get('team2', {}).get('name', 'Unknown Team 2')
        stats = context.get('stats', {})
        weather = context.get('weather', {})
        insights = context.get('insights', {})
        text = context.get('text', '')

        team1_stats = stats.get('team1', {})
        team2_stats = stats.get('team2', {})

        insights_str = (
            f"Overall Sentiment: {insights.get('overall_sentiment', {}).get('interpretation', 'N/A')}\n"
            f"News Summary: {insights.get('news_summary', ['N/A'])}\n"
            f"Expert Opinions: {insights.get('expert_opinions', ['N/A'])}\n"
            f"Injury Notes: {insights.get('injury_notes', ['N/A'])}\n"
            f"Betting Trends: {insights.get('betting_trends', ['N/A'])}\n"
            f"Key Factors: {insights.get('key_factors', ['N/A'])}"
        )

        return f"""You are an expert sports analyst. Analyze the matchup between {team1} and {team2} and return the response in valid JSON format, enclosed in ```json\n...\n```. Do not include any additional text outside the JSON block. The JSON must follow this structure:

```json
{{
  "prediction": {{
    "winner": "{team1}",
    "confidence": 7,
    "score_range": "2-1"
  }},
  "key_factors": ["Factor 1"],
  "risk_assessment": "Medium",
  "betting_recommendations": {{
    "moneyline": "Bet on {team1} at 1.80",
    "spread": "{team1} -1.5",
    "totals": "Over 2.5"
  }},
  "insights": ["Insight 1"]
}}
```

Matchup Details:
- Teams: {team1} vs {team2}
- Sport: Soccer
- User Text: {text}
- Team 1 Stats: {team1_stats}
- Team 2 Stats: {team2_stats}
- Weather: {weather}
- Web Insights: {insights_str}

Instructions:
1. Use recent form, injuries, and betting trends from Web Insights to inform your prediction.
2. Ensure the 'winner' field is consistent with the 'score_range':
   - If the score_range indicates a draw (e.g., '1-1'), set 'winner' to 'Draw'.
   - Otherwise, set 'winner' to the team with the higher score in the score_range.
3. Provide specific key factors based on the data (e.g., 'Team X on a winning streak').
4. Base betting recommendations on implied probabilities from betting trends and expert opinions, prioritizing trends (e.g., Under/Over goals) from Web Insights.
5. If data is limited, make a best-effort prediction but note the uncertainty in the insights.

Return only the JSON response in the specified format, enclosed in ```json\n...\n```."""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured matchup analysis."""
        logger.debug(f"Attempting to parse LLM response: {response}")
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
                "prediction": {"winner": "Unknown", "confidence": 0, "score_range": "N/A"},
                "key_factors": [],
                "risk_assessment": "Unknown",
                "betting_recommendations": {"moneyline": "N/A", "spread": "N/A", "totals": "N/A"},
                "insights": []
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}", exc_info=True)
            return {
                "error": f"Unexpected error parsing LLM response: {str(e)}",
                "prediction": {"winner": "Unknown", "confidence": 0, "score_range": "N/A"},
                "key_factors": [],
                "risk_assessment": "Unknown",
                "betting_recommendations": {"moneyline": "N/A", "spread": "N/A", "totals": "N/A"},
                "insights": []
            }