import logging
from typing import Dict
import aiohttp
from ..config import Config

logger = logging.getLogger(__name__)

class SportsDataClient:
    """Client for fetching sports statistics and data."""
    
    def __init__(self):
        """Initialize the sports data client."""
        self.api_key = Config.SPORTSDB_API_KEY
        self.base_url = Config.SPORTSDB_BASE_URL
        
    async def get_player_stats(self, player_name: str) -> Dict:
        """Get player statistics from TheSportsDB API."""
        try:
            async with aiohttp.ClientSession() as session:
                # First search for the player
                search_url = f"{self.base_url}/v1/json/{self.api_key}/searchplayers.php"
                params = {'p': player_name}
                
                async with session.get(search_url, params=params) as response:
                    data = await response.json()
                    if not data.get('player'):
                        logger.warning(f"No player found for name: {player_name}")
                        return {}
                    
                    player = data['player'][0]
                    player_id = player['idPlayer']
                    
                    # Then get detailed stats
                    stats_url = f"{self.base_url}/v1/json/{self.api_key}/lookupplayer.php"
                    params = {'id': player_id}
                    
                    async with session.get(stats_url, params=params) as response:
                        stats_data = await response.json()
                        return {
                            'name': player['strPlayer'],
                            'team': player.get('strTeam', ''),
                            'position': player.get('strPosition', ''),
                            'nationality': player.get('strNationality', ''),
                            'birth_date': player.get('dateBorn', ''),
                            'description': player.get('strDescriptionEN', ''),
                            'recent_stats': stats_data.get('stats', {})
                        }
                        
        except Exception as e:
            logger.error(f"Error getting player stats: {str(e)}", exc_info=True)
            return {}
            
    async def get_team_stats(self, team_name: str) -> Dict:
        """Get team statistics from TheSportsDB API."""
        try:
            async with aiohttp.ClientSession() as session:
                # Search for the team
                search_url = f"{self.base_url}/v1/json/{self.api_key}/searchteams.php"
                params = {'t': team_name}
                
                async with session.get(search_url, params=params) as response:
                    data = await response.json()
                    if not data.get('teams'):
                        logger.warning(f"No team found for name: {team_name}")
                        return {}
                    
                    team = data['teams'][0]
                    team_id = team['idTeam']
                    
                    # Get team's last 5 events
                    events_url = f"{self.base_url}/v1/json/{self.api_key}/eventslast.php"
                    params = {'id': team_id}
                    
                    async with session.get(events_url, params=params) as response:
                        events_data = await response.json()
                        recent_events = events_data.get('results', [])
                        
                        return {
                            'name': team['strTeam'],
                            'league': team.get('strLeague', ''),
                            'stadium': team.get('strStadium', ''),
                            'description': team.get('strDescriptionEN', ''),
                            'country': team.get('strCountry', ''),
                            'recent_events': recent_events,
                            'formed_year': team.get('intFormedYear', ''),
                            'manager': team.get('strManager', '')
                        }
                        
        except Exception as e:
            logger.error(f"Error getting team stats: {str(e)}", exc_info=True)
            return {} 