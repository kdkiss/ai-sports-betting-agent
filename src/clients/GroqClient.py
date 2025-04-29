import os
import json
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime
import logging
import asyncio

# Configure logger
logger = logging.getLogger(__name__)

class GroqClient:
    """Client for interacting with the Groq API."""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
            
        self.base_url = "https://api.groq.com"
        self.model = "llama3-70b-8192"
        
        self.default_params = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.95,
            "stream": False
        }
        
        # Log event loop type
        loop = asyncio.get_event_loop()
        logger.info(f"GroqClient using event loop: {type(loop).__name__}")

    async def analyze_betting_context(
        self,
        context: Dict[str, Any],
        analysis_type: str
    ) -> Dict[str, Any]:
        """Analyze betting context using Groq."""
        prompt = self._create_analysis_prompt(context, analysis_type)
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert sports betting analyst with deep knowledge of statistics, odds analysis, and risk assessment."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = await self._make_api_call(messages)
            return self._parse_analysis_response(response, analysis_type)
        except Exception as e:
            logger.error(f"Error in Groq analysis: {e}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_analysis_prompt(
        self,
        context: Dict[str, Any],
        analysis_type: str
    ) -> str:
        """Create appropriate prompt based on analysis type."""
        if analysis_type == "parlay":
            return self._create_parlay_prompt(context)
        elif analysis_type == "player_props":
            return self._create_player_props_prompt(context)
        elif analysis_type == "game_analysis":
            return self._create_game_analysis_prompt(context)
        else:
            return self._create_general_analysis_prompt(context)
    
    def _create_parlay_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for parlay analysis."""
        return f"""Analyze this parlay bet with the following context:
        Sport(s): {context.get('sport', 'Unknown')}
        Teams/Players: {context.get('teams', [])}
        Bet Types: {context.get('bet_types', [])}
        Odds: {context.get('odds', 'Not provided')}
        
        Additional Context:
        - Weather: {context.get('weather', 'Not applicable')}
        - Injuries: {context.get('injuries', 'No data')}
        - Recent Performance: {context.get('recent_performance', 'No data')}
        
        Please provide:
        1. Risk assessment
        2. Expected value analysis
        3. Key factors affecting outcomes
        4. Correlation between legs
        5. Recommendation with confidence level
        
        Format the response as JSON."""
    
    def _create_player_props_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for player props analysis."""
        return f"""Analyze this player prop bet:
        Player: {context.get('player', 'Unknown')}
        Sport: {context.get('sport', 'Unknown')}
        Prop Type: {context.get('prop_type', 'Unknown')}
        Line: {context.get('line', 'Not provided')}
        
        Consider:
        - Recent performance trends
        - Matchup specifics
        - Team dynamics
        - Historical performance
        
        Provide analysis in JSON format including:
        1. Probability assessment
        2. Risk factors
        3. Value rating
        4. Confidence score
        5. Recommendation"""
    
    def _create_game_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for game analysis."""
        return f"""Analyze this game with betting context:
        Sport: {context.get('sport', 'Unknown')}
        Teams: {context.get('teams', [])}
        Market: {context.get('market_type', 'Unknown')}
        
        Factors to consider:
        - Head-to-head history
        - Recent form
        - Injuries/Roster changes
        - Venue/Weather
        - Public betting trends
        
        Provide detailed JSON analysis including:
        1. Win probability
        2. Key matchups
        3. Risk assessment
        4. Value proposition
        5. Betting recommendation"""
    
    def _create_general_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for general betting analysis."""
        return f"""Analyze this betting opportunity:
        Context: {json.dumps(context, indent=2)}
        
        Provide comprehensive analysis in JSON format including:
        1. Risk assessment
        2. Value analysis
        3. Key factors
        4. Confidence level
        5. Recommendation"""
    
    async def _make_api_call(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Make API call to Groq."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            **self.default_params
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/openai/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in Groq API call: {e}", exc_info=True)
            raise Exception(f"API call failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Groq API call: {e}", exc_info=True)
            raise Exception(f"API call failed: {str(e)}")
    
    def _parse_analysis_response(
        self,
        response: Dict[str, Any],
        analysis_type: str
    ) -> Dict[str, Any]:
        """Parse and structure the API response."""
        try:
            content = response['choices'][0]['message']['content']
            analysis = json.loads(content)
            
            analysis['timestamp'] = datetime.now().isoformat()
            analysis['analysis_type'] = analysis_type
            
            return analysis
        except Exception as e:
            logger.error(f"Error parsing response: {e}", exc_info=True)
            return {
                "error": "Failed to parse analysis response",
                "raw_content": response.get('choices', [{}])[0].get('message', {}).get('content'),
                "timestamp": datetime.now().isoformat()
            }