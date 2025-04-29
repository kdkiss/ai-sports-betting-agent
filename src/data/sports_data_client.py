import logging
import re
from typing import Dict, Any, Optional, List
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class SportsDataClient:
    """Client for fetching sports data from TheSportsDB API."""

    def __init__(self, api_key: str):
        """Initialize the sports data client with API key."""
        self.api_key = api_key
        self.base_url = "https://www.thesportsdb.com/api/v1/json/3"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _fetch(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fetch data from TheSportsDB API."""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug(f"Fetched data from {url}: {data}")
                return data
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {e}", exc_info=True)
            return {}

    async def get_stats(self, sport: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch team stats for a given sport and context."""
        team1 = context.get('team1', {}).get('name', '')
        team2 = context.get('team2', {}).get('name', '')

        if not team1 or not team2:
            logger.warning("Missing team names in context for stats")
            return {'team1': {}, 'team2': {}}

        try:
            # Fetch team IDs
            team1_data = await self._fetch("searchteams.php", {'t': team1})
            team2_data = await self._fetch("searchteams.php", {'t': team2})

            team1_id = team1_data.get('teams', [{}])[0].get('idTeam', '')
            team2_id = team2_data.get('teams', [{}])[0].get('idTeam', '')

            if not team1_id or not team2_id:
                logger.warning(f"Could not find team IDs for {team1} or {team2}")
                return {'team1': {}, 'team2': {}}

            # Fetch recent events for both teams
            team1_events = await self._fetch("eventslast.php", {'id': team1_id})
            team2_events = await self._fetch("eventslast.php", {'id': team2_id})

            team1_stats = self._parse_team_stats(team1_events, team1)
            team2_stats = self._parse_team_stats(team2_events, team2)

            return {
                'team1': team1_stats,
                'team2': team2_stats
            }
        except Exception as e:
            logger.error(f"Error fetching stats for {team1} vs {team2}: {e}", exc_info=True)
            return {'team1': {}, 'team2': {}}

    def _parse_team_stats(self, events: Dict[str, Any], team_name: str) -> Dict[str, Any]:
        """Parse team stats from events data."""
        results = events.get('results', [])
        if not results:
            return {'recent_form': 'N/A', 'goals_scored': 0, 'goals_conceded': 0}

        wins = 0
        losses = 0
        goals_scored = 0
        goals_conceded = 0

        for event in results:
            home_team = event.get('strHomeTeam', '')
            away_team = event.get('strAwayTeam', '')
            home_score = int(event.get('intHomeScore', 0) or 0)
            away_score = int(event.get('intAwayScore', 0) or 0)

            if home_team.lower() == team_name.lower():
                goals_scored += home_score
                goals_conceded += away_score
                if home_score > away_score:
                    wins += 1
                elif home_score < away_score:
                    losses += 1
            elif away_team.lower() == team_name.lower():
                goals_scored += away_score
                goals_conceded += home_score
                if away_score > home_score:
                    wins += 1
                elif away_score < home_score:
                    losses += 1

        recent_form = f"W{wins}-L{losses}"
        return {
            'recent_form': recent_form,
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded
        }

    async def get_odds(self, sport: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch betting odds for a given sport and context (mock implementation)."""
        team1 = context.get('team1', {}).get('name', '')
        team2 = context.get('team2', {}).get('name', '')

        if not team1 or not team2:
            logger.warning("Missing team names in context for odds")
            return {}

        # Mock odds data (replace with actual API call if available)
        text = context.get('text', '')
        odds = self._parse_odds_from_text(text)
        if odds:
            return odds

        # Fallback mock odds
        return {
            'moneyline': f"{team1} 1.80, {team2} 2.10",
            'btts': {'yes': 1.75, 'no': 2.00}
        }

    def _parse_odds_from_text(self, text: str) -> Dict[str, Any]:
        """Parse odds from raw text (e.g., from OCR output)."""
        if not text:
            return {}

        lines = text.strip().split('\n')
        odds = {}
        i = 0
        while i < len(lines):
            line = lines[i].strip().lower()
            if 'moneyline' in line:
                i += 1
                if i < len(lines):
                    odds['moneyline'] = lines[i].strip()
            elif 'to score' in line:
                odds['btts'] = {
                    'yes': float(lines[i+2]) if i+2 < len(lines) and 'yes' in lines[i+1].lower() else 0.0,
                    'no': float(lines[i+4]) if i+4 < len(lines) and 'no' in lines[i+3].lower() else 0.0
                }
                i += 4
            elif 'match goals' in line:
                over_under = {}
                i += 1
                while i < len(lines):
                    if re.match(r'^\d+\.\d+$', lines[i].strip()):
                        goal_line = float(lines[i].strip())
                        i += 1
                        if i < len(lines) and 'over' in lines[i].lower():
                            i += 1
                            if i < len(lines) and re.match(r'^-?\d+\.\d+$', lines[i].strip()):
                                over_under[f"over_{goal_line}"] = float(lines[i].strip())
                                i += 1
                        if i < len(lines) and 'under' in lines[i].lower():
                            i += 1
                            if i < len(lines) and re.match(r'^-?\d+\.\d+$', lines[i].strip()):
                                over_under[f"under_{goal_line}"] = float(lines[i].strip())
                                i += 1
                    else:
                        break
                odds['over_under'] = over_under
            else:
                i += 1
        return odds