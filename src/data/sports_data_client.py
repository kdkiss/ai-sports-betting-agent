from typing import Dict, Any, Optional
import aiohttp
from datetime import datetime, timedelta
import os

class SportsDataClient:
    """Client for fetching sports statistics and data."""
    
    def __init__(self):
        self.api_key = os.getenv('SPORTS_DATA_API_KEY')
        self.base_url = "https://api.sportsdata.io/v3"
        self.cache = {}  # Simple in-memory cache
        
    async def get_stats(self, sport: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant statistics based on sport and context."""
        if 'player' in context:
            return await self._get_player_stats(sport, context)
        elif 'team' in context:
            return await self._get_team_stats(sport, context)
        else:
            return await self._get_game_stats(sport, context)
    
    async def _get_player_stats(self, sport: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get player statistics."""
        player = context['player']
        cache_key = f"{sport}_{player}_stats"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=1):
                return data
        
        # Construct API endpoint based on sport
        endpoint = self._get_player_endpoint(sport, player)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/{endpoint}",
                headers={"Ocp-Apim-Subscription-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    processed_data = self._process_player_stats(sport, data)
                    
                    # Cache the results
                    self.cache[cache_key] = (datetime.now(), processed_data)
                    return processed_data
                else:
                    return {"error": f"Failed to fetch player stats: {response.status}"}
    
    async def _get_team_stats(self, sport: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get team statistics."""
        team = context['team']
        cache_key = f"{sport}_{team}_stats"
        
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=1):
                return data
        
        endpoint = self._get_team_endpoint(sport, team)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/{endpoint}",
                headers={"Ocp-Apim-Subscription-Key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    processed_data = self._process_team_stats(sport, data)
                    self.cache[cache_key] = (datetime.now(), processed_data)
                    return processed_data
                else:
                    return {"error": f"Failed to fetch team stats: {response.status}"}
    
    def _get_player_endpoint(self, sport: str, player: str) -> str:
        """Get the appropriate API endpoint for player stats."""
        endpoints = {
            'NFL': f'nfl/stats/json/PlayerSeasonStats/{self._get_season()}',
            'NBA': f'nba/stats/json/PlayerSeasonStats/{self._get_season()}',
            'MLB': f'mlb/stats/json/PlayerSeasonStats/{self._get_season()}',
            'NHL': f'nhl/stats/json/PlayerSeasonStats/{self._get_season()}',
            'UFC': f'mma/stats/json/Fighter/{player}'
        }
        return endpoints.get(sport, '')
    
    def _get_team_endpoint(self, sport: str, team: str) -> str:
        """Get the appropriate API endpoint for team stats."""
        endpoints = {
            'NFL': f'nfl/stats/json/TeamSeasonStats/{self._get_season()}',
            'NBA': f'nba/stats/json/TeamSeasonStats/{self._get_season()}',
            'MLB': f'mlb/stats/json/TeamSeasonStats/{self._get_season()}',
            'NHL': f'nhl/stats/json/TeamSeasonStats/{self._get_season()}'
        }
        return endpoints.get(sport, '')
    
    def _get_season(self) -> str:
        """Get current season year."""
        now = datetime.now()
        if now.month < 7:  # Assuming seasons start in second half of year
            return str(now.year - 1)
        return str(now.year)
    
    def _process_player_stats(self, sport: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw player stats into standardized format."""
        # Implementation would vary by sport
        return {
            'raw_data': data,
            'processed': True,
            'last_updated': datetime.now().isoformat()
        }
    
    def _process_team_stats(self, sport: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw team stats into standardized format."""
        # Implementation would vary by sport
        return {
            'raw_data': data,
            'processed': True,
            'last_updated': datetime.now().isoformat()
        } 