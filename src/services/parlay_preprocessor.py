from typing import Dict, List
import re

class ParlayPreprocessor:
    """Preprocesses and formats parlay text for analysis."""
    
    def __init__(self):
        self.bet_indicators = {
            'total_points': [
                'total points',
                'over',
                'under'
            ],
            'touchdown': [
                'touchdown scorer',
                'anytime touchdown',
                '1st touchdown',
                'to score'
            ],
            'player_stats': [
                'passing yards',
                'rushing yards',
                'receiving yards',
                'passing touchdowns'
            ]
        }
    
    def preprocess(self, text: str) -> str:
        """Clean and format parlay text for analysis."""
        # Split into lines and remove empty ones
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        formatted_bets = []
        current_bet = {}
        last_player = None
        last_prop_type = None
        
        i = 0
        while i < len(lines):
            line = lines[i].lower()
            
            # Skip metadata lines
            if self._is_metadata(line):
                i += 1
                continue
            
            # Look for bet type indicators first
            if 'total points' in line:
                last_prop_type = 'total'
                if 'chiefs' in line:
                    current_bet = {'type': 'total', 'team': 'Kansas City Chiefs'}
                else:
                    current_bet = {'type': 'total'}
            elif 'touchdown' in line:
                last_prop_type = 'touchdown'
                if '1st' in line or 'first' in line:
                    current_bet = {'type': 'player_prop', 'prop': 'first_touchdown'}
                else:
                    current_bet = {'type': 'player_prop', 'prop': 'anytime_touchdown'}
            elif 'passing yards' in line:
                last_prop_type = 'passing_yards'
                current_bet = {'type': 'player_prop', 'prop': 'passing_yards'}
            elif 'passing touchdowns' in line:
                last_prop_type = 'passing_td'
                current_bet = {'type': 'player_prop', 'prop': 'passing_touchdowns'}
            
            # Look for player information
            player_info = self._extract_player_info(line)
            if player_info['name']:
                last_player = player_info
                if current_bet:
                    current_bet.update({
                        'player': player_info['name'],
                        'team': player_info['team']
                    })
            
            # Look for numbers (lines/totals)
            if 'over' in line:
                number = self._extract_number(line)
                if number is not None:
                    current_bet['line'] = number
            
            # Handle odds changes and standalone odds
            odds = None
            if 'odds have' in line:
                odds = self._extract_new_odds(line)
            else:
                odds_match = re.search(r'[+-]\d+', line)
                if odds_match:
                    odds = odds_match.group()
            
            # If we found odds and have a current bet or last player
            if odds:
                if not current_bet and last_player and last_prop_type:
                    # Reconstruct bet from last known info
                    current_bet = {
                        'type': 'player_prop',
                        'prop': last_prop_type,
                        'player': last_player['name'],
                        'team': last_player['team']
                    }
                
                if current_bet:
                    current_bet['odds'] = odds
                    formatted_bets.append(self._format_bet(current_bet))
                    current_bet = {}
            
            i += 1
        
        # Format into analyzer-friendly text
        result = self._combine_bets(formatted_bets)
        if not result:
            raise ValueError("No valid bets found in slip")
        return result
    
    def _is_metadata(self, line: str) -> bool:
        """Check if line is metadata."""
        metadata_terms = [
            'risk', 'win', 'bet max', 'cash out', 'available', 'selection',
            'suspended', 'max'
        ]
        return any(term in line.lower() for term in metadata_terms)
    
    def _extract_new_odds(self, line: str) -> str:
        """Extract new odds from odds change line."""
        match = re.search(r'to ([+-]\d+)', line)
        return match.group(1) if match else None
    
    def _extract_number(self, line: str) -> float:
        """Extract number from line."""
        match = re.search(r'\d+\.?\d*', line)
        return float(match.group()) if match else None
    
    def _extract_player_info(self, line: str) -> Dict:
        """Extract player name and team."""
        match = re.search(r'(.+?)\s*\((\w+)\)', line)
        if match:
            return {
                'name': match.group(1).strip(),
                'team': match.group(2).strip()
            }
        return {'name': None, 'team': None}
    
    def _format_bet(self, bet: Dict) -> str:
        """Format a single bet into analyzer-friendly text."""
        if not bet.get('odds'):
            return ""
            
        if bet['type'] == 'total':
            team_str = f" - {bet['team']}" if bet.get('team') else ""
            return f"Total Points{team_str}: Over {bet.get('line', '0')} ({bet['odds']})"
        elif bet['type'] == 'player_prop':
            if 'touchdown' in bet.get('prop', ''):
                return f"{bet['player']} ({bet['team']}) to score TD ({bet['odds']})"
            else:
                return f"{bet['player']} ({bet['team']}) {bet['prop']} Over {bet.get('line', '0')} ({bet['odds']})"
        return ""
    
    def _combine_bets(self, bets: List[str]) -> str:
        """Combine formatted bets into final text."""
        valid_bets = [bet for bet in bets if bet]
        if not valid_bets:
            return ""
        return "\n".join(valid_bets) 