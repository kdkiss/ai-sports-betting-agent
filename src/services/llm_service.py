from typing import Dict, List, Any
import aiohttp
from ..config import Config

class DeepSeekLLM:
    """Service for interacting with DeepSeek LLM API."""
    
    def __init__(self, api_key: str = Config.DEEPSEEK_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        
    async def analyze_bet(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a bet using DeepSeek LLM."""
        prompt = self._create_bet_analysis_prompt(context)
        response = await self._generate(prompt)
        return self._parse_betting_analysis(response)
    
    async def analyze_team_matchup(self, team1_data: Dict, team2_data: Dict) -> Dict[str, Any]:
        """Analyze team matchup using historical data and current form."""
        prompt = self._create_matchup_analysis_prompt(team1_data, team2_data)
        response = await self._generate(prompt)
        return self._parse_matchup_analysis(response)
    
    async def generate_betting_strategy(self, parlay_data: Dict) -> Dict[str, Any]:
        """Generate optimal betting strategy based on parlay analysis."""
        prompt = self._create_strategy_prompt(parlay_data)
        response = await self._generate(prompt)
        return self._parse_strategy_recommendations(response)

    def _create_bet_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Create a detailed prompt for bet analysis."""
        return f"""Analyze this betting opportunity with the following context:

Team Information:
{context.get('team_info', '')}

Historical Performance:
{context.get('historical_data', '')}

Current Form:
{context.get('current_form', '')}

Betting Details:
- Type: {context.get('bet_type', '')}
- Odds: {context.get('odds', '')}
- Line: {context.get('line', '')}

Consider:
1. Team strength and recent performance
2. Head-to-head history
3. Key player availability
4. Value assessment
5. Risk factors

Provide a detailed analysis including:
1. Confidence rating (1-10)
2. Key factors influencing the bet
3. Risk assessment
4. Value analysis
5. Specific recommendations
"""

    def _create_matchup_analysis_prompt(self, team1_data: Dict, team2_data: Dict) -> str:
        """Create a prompt for analyzing team matchups."""
        return f"""Analyze this matchup between:

Team 1: {team1_data.get('name')}
- League Position: {team1_data.get('position')}
- Recent Form: {team1_data.get('form')}
- Key Stats: {team1_data.get('stats')}

Team 2: {team2_data.get('name')}
- League Position: {team2_data.get('position')}
- Recent Form: {team2_data.get('form')}
- Key Stats: {team2_data.get('stats')}

Consider:
1. Head-to-head record
2. Current form
3. Team strengths/weaknesses
4. Key player matchups
5. Tactical analysis

Provide insights on:
1. Likely outcome
2. Key factors
3. Betting implications
4. Risk assessment
"""

    def _create_strategy_prompt(self, parlay_data: Dict) -> str:
        """Create a prompt for generating betting strategy."""
        return f"""Analyze this parlay and generate a betting strategy:

Parlay Details:
{parlay_data.get('details')}

Individual Legs:
{parlay_data.get('legs')}

Current Analysis:
{parlay_data.get('current_analysis')}

Provide strategic recommendations including:
1. Overall parlay assessment
2. Individual leg analysis
3. Risk management strategy
4. Alternative betting approaches
5. Specific actionable advice
"""

    async def _generate(self, prompt: str) -> str:
        """Make API call to DeepSeek LLM."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    raise Exception(f"API call failed with status {response.status}")

    def _parse_betting_analysis(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response for bet analysis."""
        # Implement parsing logic based on the response format
        # This is a placeholder implementation
        return {
            'confidence': 7,
            'key_factors': ['Recent form', 'Head-to-head record'],
            'risk_level': 'Medium',
            'value_assessment': 'Positive',
            'recommendations': ['Proceed with caution', 'Consider hedging']
        }

    def _parse_matchup_analysis(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response for matchup analysis."""
        # Implement parsing logic based on the response format
        return {
            'predicted_outcome': 'Team 1 advantage',
            'key_factors': ['Superior form', 'Home advantage'],
            'betting_implications': ['Value on money line'],
            'risk_assessment': 'Low'
        }

    def _parse_strategy_recommendations(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response for strategy recommendations."""
        # Implement parsing logic based on the response format
        return {
            'overall_assessment': 'Positive',
            'leg_analysis': ['Leg 1: Strong', 'Leg 2: Moderate'],
            'risk_management': ['Split into single bets', 'Reduce stake'],
            'alternatives': ['Consider straight bets', 'Look for better lines']
        } 