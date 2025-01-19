from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime, timedelta
import os

class OddsClient:
    """Client for fetching betting odds from various sources."""
    
    def __init__(self):
        self.api_key = os.getenv('ODDS_API_KEY')
        self.base_url = "https://api.the-odds-api.com/v4"
        self.cache = {}
        self.bookmakers = [
            'fanduel', 'draftkings', 'betmgm', 'caesars',
            'pointsbet', 'barstool', 'wynn'
        ]
    
    async def get_odds(self, sport: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get odds for a specific betting opportunity."""
        cache_key = self._generate_cache_key(sport, context)
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(minutes=5):  # Short cache for odds
                return data
        
        # Determine what type of odds to fetch
        if self._is_prop_bet(context):
            odds = await self._get_prop_odds(sport, context)
        else:
            odds = await self._get_game_odds(sport, context)
            
        # Cache results
        self.cache[cache_key] = (datetime.now(), odds)
        return odds
    
    async def _get_prop_odds(self, sport: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get odds for player props."""
        sport_key = self._get_sport_key(sport)
        player = context.get('player', '')
        prop_type = context.get('prop_type', '')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/sports/{sport_key}/players/{player}/markets",
                params={
                    'apiKey': self.api_key,
                    'bookmakers': ','.join(self.bookmakers)
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_prop_odds(data, prop_type)
                else:
                    return {"error": f"Failed to fetch prop odds: {response.status}"}
    
    async def _get_game_odds(self, sport: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get odds for game outcomes."""
        sport_key = self._get_sport_key(sport)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/sports/{sport_key}/odds",
                params={
                    'apiKey': self.api_key,
                    'regions': 'us',
                    'markets': 'h2h,spreads,totals',
                    'bookmakers': ','.join(self.bookmakers)
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_game_odds(data, context)
                else:
                    return {"error": f"Failed to fetch game odds: {response.status}"}
    
    def _get_sport_key(self, sport: str) -> str:
        """Convert internal sport name to API sport key."""
        sport_keys = {
            'NFL': 'americanfootball_nfl',
            'NBA': 'basketball_nba',
            'MLB': 'baseball_mlb',
            'NHL': 'icehockey_nhl',
            'UFC': 'mma_mixed_martial_arts',
            'Soccer': 'soccer_epl'  # Default to EPL, can be expanded
        }
        return sport_keys.get(sport, '')
    
    def _generate_cache_key(self, sport: str, context: Dict[str, Any]) -> str:
        """Generate cache key based on sport and context."""
        if self._is_prop_bet(context):
            return f"{sport}_prop_{context.get('player', '')}_{context.get('prop_type', '')}"
        return f"{sport}_game_{context.get('team', '')}"
    
    def _is_prop_bet(self, context: Dict[str, Any]) -> bool:
        """Determine if context is for a prop bet."""
        return 'player' in context and 'prop_type' in context
    
    def _process_prop_odds(self, data: Dict[str, Any], prop_type: str) -> Dict[str, Any]:
        """Process raw prop odds data into standardized format."""
        processed = {
            'best_over': {'odds': -110, 'book': ''},
            'best_under': {'odds': -110, 'book': ''},
            'market_info': {
                'last_update': datetime.now().isoformat(),
                'num_books': 0,
                'consensus_line': 0,
                'line_movement': []
            }
        }
        
        if 'markets' in data:
            for market in data['markets']:
                if market['market_type'].lower() == prop_type.lower():
                    processed['market_info']['num_books'] += 1
                    for outcome in market['outcomes']:
                        if 'over' in outcome['name'].lower():
                            if self._better_odds(outcome['price'], processed['best_over']['odds']):
                                processed['best_over'] = {
                                    'odds': outcome['price'],
                                    'book': market['bookmaker']
                                }
                        elif 'under' in outcome['name'].lower():
                            if self._better_odds(outcome['price'], processed['best_under']['odds']):
                                processed['best_under'] = {
                                    'odds': outcome['price'],
                                    'book': market['bookmaker']
                                }
        
        return processed
    
    def _process_game_odds(self, data: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw game odds data into standardized format."""
        processed = {
            'moneyline': {'home': {}, 'away': {}},
            'spread': {'home': {}, 'away': {}},
            'total': {'over': {}, 'under': {}},
            'market_info': {
                'last_update': datetime.now().isoformat(),
                'num_books': len(data),
                'line_movement': []
            }
        }
        
        for game in data:
            if self._matches_context(game, context):
                for bookmaker in game['bookmakers']:
                    for market in bookmaker['markets']:
                        self._update_best_odds(processed, market, bookmaker['key'])
                break
        
        return processed
    
    def _better_odds(self, new_odds: float, current_odds: float) -> bool:
        """Determine if new odds are better than current odds."""
        if new_odds > 0 and current_odds > 0:
            return new_odds > current_odds
        if new_odds < 0 and current_odds < 0:
            return new_odds > current_odds
        return new_odds > 0  # Positive odds are better than negative
    
    def _matches_context(self, game: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if game data matches the context we're looking for."""
        team = context.get('team', '').lower()
        return (team in game['home_team'].lower() or 
                team in game['away_team'].lower()) 