from typing import Dict, Any, List
from .base_agent import BaseAgent
import json
import re
import logging
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

class ParlayAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing parlay bets."""

    def __init__(self, llm, search_client, sports_data_client=None):
        """Initialize the agent with LLM service, search client, and sports data client."""
        super().__init__(llm=llm, sports_data_client=sports_data_client)
        self.search_client = search_client

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a parlay bet."""
        try:
            text = context.get('text', '')
            logger.debug(f"OCR output text: {text}")
            
            bets = self._parse_bets(text)
            teams = self._extract_teams(text)
            if not bets:
                logger.error("No valid bets found to analyze")
                raise ValueError("No valid bets found to analyze")
            
            # Fallback for missing teams
            context['team1'] = {'name': teams[0] if teams else 'Unknown Team 1'}
            context['team2'] = {'name': teams[1] if len(teams) > 1 else 'Unknown Team 2'}
            context['bets'] = bets
            logger.debug(f"Extracted teams: {context['team1']['name']} vs {context['team2']['name']}")

            odds = await self.sports_data.get_odds('Soccer', context) if self.sports_data else {}
            context['odds'] = odds

            insights = await self.search_client.gather_insights(context)
            if not insights or 'overall_sentiment' not in insights:
                logger.warning("SearchClient returned empty or invalid insights")
                insights = {
                    'overall_sentiment': {'interpretation': 'Neutral'},
                    'news_summary': ['No recent news available'],
                    'expert_opinions': ['No expert opinions available'],
                    'injury_notes': ['No injury notes available'],
                    'betting_trends': ['No betting trends available'],
                    'key_factors': ['Limited data available']
                }
            context['insights'] = insights
            logger.debug(f"Fetched insights for parlay: {insights}")

            response = await self._get_llm_analysis(context)
            parsed_response = self._parse_response(response)
            if "error" in parsed_response:
                logger.error(f"Failed to parse LLM response: {parsed_response['error']}")
                raise ValueError(f"LLM parsing error: {parsed_response['error']}")
            parsed_response = self._format_analysis(parsed_response)
            return parsed_response
        except Exception as e:
            logger.error(f"Error in parlay analysis: {e}", exc_info=True)
            return {
                "error": f"Failed to analyze parlay: {str(e)}",
                "raw_response": context.get('text', ''),
                "overall_rating": {"confidence": 0, "risk_level": "Unknown", "expected_value": "0%"},
                "analysis": {"strengths": [], "concerns": []},
                "recommendations": {"primary": "N/A", "alternatives": []},
                "bankroll_advice": {"recommended_stake": "N/A", "max_risk": "N/A"}
            }

    def _extract_teams(self, text: str) -> List[str]:
        """Extract team names from text using fuzzy matching."""
        known_teams = [
            'juventus', 'monza', 'atalanta', 'lecce', 'bournemouth', 'man utd',
            'manchester united', 'udinese', 'bologna', 'napoli', 'torino', 'empoli',
            'inter milan', 'ac milan', 'fiorentina'
        ]
        text_lower = text.lower()
        found_teams = []

        words = text_lower.split()
        for word in words:
            for team in known_teams:
                if fuzz.ratio(word, team) > 85:
                    if team not in found_teams:
                        found_teams.append(team)
                        break

        if 'bolbgna' in text_lower and 'bologna' not in found_teams:
            found_teams.append('bologna')

        logger.debug(f"Extracted teams: {found_teams}")
        return found_teams[:2]

    def _parse_bets(self, text: str) -> List[Dict[str, Any]]:
        """Parse raw text to extract bets with improved OCR error handling."""
        bets = []
        lines = text.strip().split('\n')
        current_bet_type = None
        teams = self._extract_teams(text)
        odds_buffer = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip().lower()
            line = (line.replace('t0 score', 'to score')
                    .replace('teamsto score', 'to score')
                    .replace('bothteams score', 'to score')
                    .replace('bothteams', 'to score')
                    .replace('drawno bet', 'draw no bet')
                    .replace('match gcals', 'match goals')
                    .replace('bel365', 'bet365'))
            
            if any(keyword in line for keyword in [
                'full-time', 'double chance', '1st half', 'draw no bet', 
                'to score', 'match goals'
            ]):
                if current_bet_type and odds_buffer and teams:
                    bets.append({
                        "teams": teams[:2],
                        "bet_type": current_bet_type,
                        "odds": odds_buffer
                    })
                current_bet_type = line
                odds_buffer = []
                i += 1
            elif current_bet_type == 'match goals' and line in ['over', 'under']:
                option = line
                i += 1
                if i < len(lines) and re.match(r'^~?\d+\.\d{2}$|^\d+\.\d{2}\s+\d+\.\d{2}$|^\d+$', lines[i].strip()):
                    try:
                        odds_value = float(lines[i].strip())
                        if odds_value > 50:
                            odds_value = odds_value / 100
                        if odds_value >= 1.0:
                            odds_buffer.append({option: odds_value})
                    except ValueError:
                        logger.debug(f"Skipping invalid odds for {option}: {lines[i]}")
                    i += 1
            elif current_bet_type == 'to score' and line in ['yes', 'no']:
                option = line
                i += 1
                if i < len(lines) and re.match(r'^~?\d+\.\d{2}$|^\d+$', lines[i].strip()):
                    try:
                        odds_value = float(lines[i].strip())
                        if odds_value > 50:
                            odds_value = odds_value / 100
                        if odds_value >= 1.0:
                            odds_buffer.append({option: odds_value})
                    except ValueError:
                        logger.debug(f"Skipping invalid odds for {option}: {lines[i]}")
                    i += 1
            elif re.match(r'^~?\d+\.\d{2}$|^\d+\.\d{2}\s+\d+\.\d{2}$|^\d+$', line):
                try:
                    odds = [float(o) for o in line.split() if float(o) >= 1.0]
                    odds = [o / 100 if o > 50 else o for o in odds]
                    odds_buffer.extend(odds)
                except ValueError:
                    logger.debug(f"Skipping invalid odds line: {line}")
                i += 1
            else:
                i += 1
        
        if current_bet_type and odds_buffer and teams:
            bets.append({
                "teams": teams[:2],
                "bet_type": current_bet_type,
                "odds": odds_buffer
            })
        
        logger.debug(f"Parsed bets: {bets}")
        return bets

    def _create_prompt(self, context: Dict[str, Any]) -> str:
        """Create a prompt for parlay analysis."""
        text = context.get('text', '')
        bets = context.get('bets', [])
        odds = context.get('odds', {})
        insights = context.get('insights', {})
        
        bet_details = "\n".join([
            f"- Teams: {bet['teams']}, Bet Type: {bet['bet_type']}, Odds: {bet['odds']}"
            for bet in bets
        ]) if bets else "No structured bets parsed."
        
        odds_details = (
            f"Moneyline: {odds.get('moneyline', 'N/A')}\n"
            f"Both Teams to Score: {odds.get('btts', 'N/A')}"
        ) if odds else "No odds available."

        insights_str = (
            f"Overall Sentiment: {insights.get('overall_sentiment', {}).get('interpretation', 'N/A')}\n"
            f"News Summary: {insights.get('news_summary', ['N/A'])}\n"
            f"Expert Opinions: {insights.get('expert_opinions', ['N/A'])}\n"
            f"Injury Notes: {insights.get('injury_notes', ['N/A'])}\n"
            f"Betting Trends: {insights.get('betting_trends', ['N/A'])}\n"
            f"Key Factors: {insights.get('key_factors', ['N/A'])}"
        )

        team1 = context.get('team1', {}).get('name', 'Unknown Team 1')
        team2 = context.get('team2', {}).get('name', 'Unknown Team 2')

        return f"""You are an expert sports betting analyst. Analyze the following parlay or betting slip and return the response in valid JSON format, enclosed in ```json\n...\n```. Do not include any additional text outside the JSON block. The JSON must follow this exact structure:

```json
{{
  "overall_rating": {{
    "confidence": 7,
    "risk_level": "Medium",
    "expected_value": "10%"
  }},
  "analysis": {{
    "strengths": ["Strength 1"],
    "concerns": ["Concern 1"]
  }},
  "recommendations": {{
    "primary": "Recommendation",
    "alternatives": ["Alternative 1"]
  }},
  "bankroll_advice": {{
    "recommended_stake": "$100",
    "max_risk": "5%"
  }}
}}
```

Parlay/Betting Slip Details:
```
{text}
```

Teams (if identified):
- Team 1: {team1}
- Team 2: {team2}

Parsed Bets:
{bet_details}

Available Odds:
{odds_details}

Web Insights:
{insights_str}

Consider:
1. Implied probabilities from odds.
2. Team performance and match context from Web Insights (if available).
3. Prioritize betting trends (e.g., Under/Over goals, Both Teams to Score) from Web Insights when making recommendations.
4. Risk-reward balance and market efficiency.
5. Correlation between bets.
6. If teams are unknown or Web Insights are limited, make a best-effort analysis based on the odds and bet types, and note the uncertainty in the 'concerns' section.

Return only the JSON response in the specified format, enclosed in ```json\n...\n```."""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured parlay analysis."""
        logger.debug(f"Raw LLM response for parlay: {response}")
        try:
            json_match = re.search(r'```json\n([\s\S]*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)
            else:
                parsed = json.loads(response)

            required_fields = ['overall_rating', 'analysis', 'recommendations', 'bankroll_advice']
            missing_fields = [field for field in required_fields if field not in parsed]
            if missing_fields:
                logger.error(f"Missing required fields in LLM response: {missing_fields}")
                return {
                    "error": f"Missing required fields: {missing_fields}",
                    "raw_response": response
                }

            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}", exc_info=True)
            return {
                "error": "Failed to parse LLM response as JSON",
                "raw_response": response
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}", exc_info=True)
            return {
                "error": f"Unexpected error parsing LLM response: {str(e)}",
                "raw_response": response
            }

    def _format_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format analysis results in a standardized way."""
        try:
            required_fields = ['overall_rating', 'analysis', 'recommendations', 'bankroll_advice']
            missing_fields = [field for field in required_fields if field not in analysis]
            if missing_fields:
                logger.error(f"Incomplete analysis data, missing fields: {missing_fields}")
                raise ValueError(f"Incomplete analysis data, missing fields: {missing_fields}")

            if 'confidence' not in analysis['overall_rating'] or \
               'risk_level' not in analysis['overall_rating'] or \
               'expected_value' not in analysis['overall_rating']:
                logger.error("Missing fields in overall_rating")
                raise ValueError("Missing fields in overall_rating")

            if 'strengths' not in analysis['analysis'] or 'concerns' not in analysis['analysis']:
                logger.error("Missing fields in analysis section")
                raise ValueError("Missing fields in analysis section")

            if 'primary' not in analysis['recommendations'] or 'alternatives' not in analysis['recommendations']:
                logger.error("Missing fields in recommendations")
                raise ValueError("Missing fields in recommendations")

            if 'recommended_stake' not in analysis['bankroll_advice'] or 'max_risk' not in analysis['bankroll_advice']:
                logger.error("Missing fields in bankroll_advice")
                raise ValueError("Missing fields in bankroll_advice")

            return {
                "overall_rating": analysis['overall_rating'],
                "analysis": analysis['analysis'],
                "recommendations": analysis['recommendations'],
                "bankroll_advice": analysis['bankroll_advice']
            }
        except Exception as e:
            logger.error(f"Error formatting parlay analysis: {e}", exc_info=True)
            raise ValueError("Incomplete or invalid data returned")