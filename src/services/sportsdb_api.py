import aiohttp
from typing import Dict, List, Optional
from ..config import Config

class SportsDBAPI:
    BASE_URL = "https://www.thesportsdb.com/api/v1/json"
    
    def __init__(self, api_key: str = Config.SPORTSDB_API_KEY):
        self.api_key = api_key
        
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make an async request to TheSportsDB API."""
        url = f"{self.BASE_URL}/{self.api_key}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                response.raise_for_status()

    async def search_team(self, team_name: str) -> List[Dict]:
        """Search for a team by name."""
        data = await self._make_request("searchteams.php", {"t": team_name})
        return data.get("teams", []) if data else []

    async def search_team_by_shortcode(self, short_code: str) -> List[Dict]:
        """Search for a team by short code."""
        data = await self._make_request("searchteams.php", {"sname": short_code})
        return data.get("teams", []) if data else []

    async def search_players(self, team_name: str = None, player_name: str = None) -> List[Dict]:
        """Search for players by team name or player name."""
        params = {}
        if team_name:
            params["t"] = team_name
        if player_name:
            params["p"] = player_name
        data = await self._make_request("searchplayers.php", params)
        return data.get("player", []) if data else []

    async def get_team_details(self, team_id: str) -> Optional[Dict]:
        """Get detailed information about a team by ID."""
        data = await self._make_request("lookupteam.php", {"id": team_id})
        teams = data.get("teams", [])
        return teams[0] if teams else None

    async def get_player_details(self, player_id: str) -> Optional[Dict]:
        """Get detailed information about a player by ID."""
        data = await self._make_request("lookupplayer.php", {"id": player_id})
        players = data.get("players", [])
        return players[0] if players else None

    async def get_team_next_events(self, team_id: str) -> List[Dict]:
        """Get next 5 events for a team."""
        data = await self._make_request("eventsnext.php", {"id": team_id})
        return data.get("events", []) if data else []

    async def get_team_last_events(self, team_id: str) -> List[Dict]:
        """Get last 5 events for a team."""
        data = await self._make_request("eventslast.php", {"id": team_id})
        return data.get("results", []) if data else []

    async def get_league_table(self, league_id: str, season: str) -> List[Dict]:
        """Get league table for a specific season."""
        data = await self._make_request("lookuptable.php", {
            "l": league_id,
            "s": season
        })
        return data.get("table", []) if data else [] 