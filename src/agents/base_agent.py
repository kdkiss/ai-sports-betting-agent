from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..clients.sports_data_client import SportsDataClient
from ..data.odds_client import OddsClient
from ..data.weather_client import WeatherClient
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

class BaseAgent(ABC):
    """Base class for all sport-specific betting agents."""
    
    def __init__(self, llm=None, sports_data_client=None, odds_client=None, weather_client=None):
        """Initialize the agent with optional LLM service and data clients."""
        self.llm = llm
        self.sports_data = sports_data_client
        self.odds_data = odds_client
        self.weather_data = weather_client
        
    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a betting opportunity.
        
        Args:
            context: Dictionary containing all relevant information for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    async def _get_llm_analysis(self, context: Dict[str, Any]) -> str:
        """Get analysis from the LLM."""
        if not self.llm:
            raise ValueError("LLM not initialized")
        
        prompt_text = self._create_prompt(context)
        prompt = PromptTemplate(input_variables=["context"], template="{context}")
        chain = prompt | self.llm
        response = await chain.ainvoke({"context": prompt_text})
        return response.content
    
    @abstractmethod
    def _create_prompt(self, context: Dict[str, Any]) -> str:
        """Create a prompt for LLM analysis."""
        pass
    
    @abstractmethod
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data."""
        pass
    
    async def _get_data(self, sport: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather all necessary data for analysis."""
        data = {}
        
        if self.odds_data:
            data['odds'] = await self.odds_data.get_odds(sport, context)
        if self.sports_data:
            data['stats'] = await self.sports_data.get_stats(sport, context)
        
        # Add weather data for outdoor sports if weather client is available
        if self.weather_data and sport in ['NFL', 'MLB']:
            data['weather'] = await self.weather_data.get_forecast(context)
            
        return data
    
    def _calculate_expected_value(self, probability: float, odds: float) -> float:
        """Calculate expected value of a bet."""
        if odds > 0:
            decimal_odds = (odds / 100) + 1
        else:
            decimal_odds = (100 / abs(odds)) + 1
            
        return (probability * (decimal_odds - 1)) - ((1 - probability) * 1)
    
    def _calculate_kelly_criterion(self, probability: float, odds: float) -> float:
        """Calculate Kelly Criterion bet size."""
        if odds > 0:
            decimal_odds = (odds / 100) + 1
        else:
            decimal_odds = (100 / abs(odds)) + 1
            
        return (probability * (decimal_odds - 1) - (1 - probability)) / (decimal_odds - 1)
    
    def _assess_risk(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk level of a bet."""
        risk_score = 0
        risk_factors = []
        
        # Example risk factors (to be customized by each agent)
        if factors.get('injury_impact', 0) > 0.3:
            risk_score += 2
            risk_factors.append('Key injuries affecting performance')
            
        if factors.get('weather_impact', 'neutral') == 'negative':
            risk_score += 1
            risk_factors.append('Adverse weather conditions')
            
        if factors.get('line_movement', 0) > 10:
            risk_score += 1
            risk_factors.append('Significant line movement')
            
        return {
            'score': risk_score,
            'level': 'High' if risk_score > 3 else 'Medium' if risk_score > 1 else 'Low',
            'factors': risk_factors
        }
    
    def _format_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format analysis results in a standardized way."""
        return {
            'recommendation': analysis.get('recommendation', 'Pass'),
            'confidence': analysis.get('confidence', 0.0),
            'expected_value': analysis.get('expected_value', 0.0),
            'risk_assessment': analysis.get('risk_assessment', {}),
            'key_factors': analysis.get('key_factors', []),
            'data_points': analysis.get('data_points', {}),
            'timestamp': analysis.get('timestamp', None)
        }