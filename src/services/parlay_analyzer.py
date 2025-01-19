from typing import Dict, List, Optional
import re
from dataclasses import dataclass
from datetime import datetime
import numpy as np

@dataclass
class BetLeg:
    team: str
    odds: float
    bet_type: str
    points: Optional[float] = None
    player: Optional[str] = None
    prop_type: Optional[str] = None
    prop_value: Optional[float] = None

@dataclass
class Parlay:
    legs: List[BetLeg]
    stake: float
    total_odds: float

class ParlayAnalyzer:
    """Analyzes parlays and provides recommendations."""
    
    def __init__(self, sports_api):
        self.sports_api = sports_api
        
        # Common patterns in bet slips
        self.patterns = {
            'total_points': r'(?:Over|Under)\s*(\d+(?:\.\d+)?)',
            'player_prop': r'(.+?)\s*\((.*?)\)',
            'odds_change': r'Odds have (?:increased|decreased) from [+-]\d+ to ([+-]\d+)',
            'odds': r'[+-]\d+',
            'player_td': r'(?:Anytime|1st) Touchdown Scorer',
            'passing_yards': r'Total Passing Yards',
            'passing_td': r'Total Passing Touchdowns'
        }
    
    async def parse_parlay_text(self, text: str) -> Parlay:
        """Parse parlay text into structured data."""
        try:
            # Split into lines and filter out empty ones
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            legs = []
            current_bet = {}
            
            i = 0
            while i < len(lines):
                line = lines[i].lower()
                
                # Skip common metadata lines
                if self._is_metadata_line(line):
                    i += 1
                    continue
                
                # Check for odds changes and get the new odds
                if 'odds have' in line:
                    odds_match = re.search(self.patterns['odds_change'], line)
                    if odds_match:
                        current_bet['odds'] = self._convert_odds(odds_match.group(1))
                    i += 1
                    continue
                
                # Look for standalone odds
                odds_match = re.search(self.patterns['odds'], line)
                if odds_match and not current_bet.get('odds'):
                    current_bet['odds'] = self._convert_odds(odds_match.group(0))
                    i += 1
                    continue
                
                # Check for total points
                total_match = re.search(self.patterns['total_points'], line)
                if total_match:
                    current_bet = {
                        'team': '',
                        'bet_type': 'total',
                        'points': float(total_match.group(1))
                    }
                    # Look ahead for odds
                    if i + 1 < len(lines) and re.search(self.patterns['odds'], lines[i + 1]):
                        current_bet['odds'] = self._convert_odds(re.search(self.patterns['odds'], lines[i + 1]).group(0))
                    if current_bet.get('odds'):
                        legs.append(BetLeg(**current_bet))
                        current_bet = {}
                    i += 1
                    continue
                
                # Check for player props
                player_match = re.search(self.patterns['player_prop'], line)
                if player_match:
                    player_name = player_match.group(1).strip()
                    team = player_match.group(2).strip()
                    prop_type = None
                    
                    # Look back for prop type
                    if i > 0:
                        prev_line = lines[i-1].lower()
                        if 'touchdown scorer' in prev_line:
                            prop_type = 'touchdown'
                        elif 'passing yards' in prev_line:
                            prop_type = 'passing_yards'
                        elif 'passing touchdowns' in prev_line:
                            prop_type = 'passing_td'
                    
                    current_bet = {
                        'team': team,
                        'player': player_name,
                        'bet_type': 'player_prop',
                        'prop_type': prop_type
                    }
                    
                    # Look ahead for odds
                    if i + 1 < len(lines) and re.search(self.patterns['odds'], lines[i + 1]):
                        current_bet['odds'] = self._convert_odds(re.search(self.patterns['odds'], lines[i + 1]).group(0))
                    
                    if current_bet.get('odds'):
                        legs.append(BetLeg(**current_bet))
                        current_bet = {}
                
                i += 1
            
            if not legs:
                raise ValueError("No valid bets found in the parlay")
            
            return Parlay(legs=legs, stake=100, total_odds=sum(leg.odds for leg in legs))
            
        except Exception as e:
            raise ValueError(f"Error parsing parlay: {str(e)}")
    
    def _is_metadata_line(self, line: str) -> bool:
        """Check if a line is metadata rather than a bet."""
        metadata_keywords = [
            'risk', 'win', 'bet max', 'selection', 'cash out',
            'in-play', 'same game parlay', 'sgp', 'available'
        ]
        return any(keyword in line.lower() for keyword in metadata_keywords)
    
    def _extract_stake(self, text: str) -> Optional[float]:
        """Extract stake amount from text."""
        stake_matches = re.findall(self.patterns['stake'], text.lower())
        if stake_matches:
            try:
                return float(stake_matches[0])
            except ValueError:
                return None
        return None
    
    def _extract_total_odds(self, text: str) -> Optional[float]:
        """Extract total odds from text."""
        odds_matches = re.findall(self.patterns['total_odds'], text.lower())
        if odds_matches:
            try:
                return self._convert_odds(odds_matches[0])
            except ValueError:
                return None
        return None
    
    def _parse_bet_line(self, line: str) -> Optional[BetLeg]:
        """Parse a single line into a bet leg."""
        try:
            # Try to match player props first
            player_prop_match = re.search(self.patterns['player_prop'], line)
            if player_prop_match:
                player, value, prop_type = player_prop_match.groups()
                return BetLeg(
                    team=self._extract_team(line),
                    odds=self._extract_odds(line),
                    bet_type='player_prop',
                    player=player.strip(),
                    prop_type=prop_type.strip(),
                    prop_value=float(value)
                )
            
            # Try spread bets
            spread_match = re.search(self.patterns['team_spread'], line)
            if spread_match:
                team, points = spread_match.groups()
                return BetLeg(
                    team=team.strip(),
                    odds=self._extract_odds(line),
                    bet_type='spread',
                    points=float(points)
                )
            
            # Try moneyline bets
            ml_match = re.search(self.patterns['money_line'], line)
            if ml_match:
                return BetLeg(
                    team=ml_match.group(1).strip(),
                    odds=self._extract_odds(line),
                    bet_type='moneyline'
                )
            
            # Try totals
            total_match = re.search(self.patterns['total_points'], line)
            if total_match:
                return BetLeg(
                    team='',  # No team for totals
                    odds=self._extract_odds(line),
                    bet_type='total',
                    points=float(total_match.group(1))
                )
            
            return None
            
        except Exception as e:
            return None
    
    def _extract_team(self, line: str) -> str:
        """Extract team name from a line."""
        # Common team indicators
        team_indicators = [' vs ', ' @ ', ' -', ' +']
        
        for indicator in team_indicators:
            if indicator in line:
                return line.split(indicator)[0].strip()
        
        return line.split()[0]  # Default to first word if no clear indicator
    
    def _extract_odds(self, line: str) -> float:
        """Extract and convert odds from a line."""
        odds_match = re.search(self.patterns['odds'], line)
        if not odds_match:
            return 0.0  # Default odds if none found
            
        return self._convert_odds(odds_match.group(0))
    
    def _convert_odds(self, odds_str: str) -> float:
        """Convert various odds formats to decimal."""
        try:
            if '/' in odds_str:
                # Fractional odds (e.g., 5/2)
                num, den = map(float, odds_str.split('/'))
                return (num / den) + 1
            elif odds_str.startswith('+'):
                # American odds positive (e.g., +150)
                return (float(odds_str) / 100) + 1
            elif odds_str.startswith('-'):
                # American odds negative (e.g., -150)
                return (100 / abs(float(odds_str))) + 1
            else:
                # Decimal odds (e.g., 2.50)
                return float(odds_str)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    async def analyze_parlay(self, parlay: Parlay) -> Dict:
        """Analyze a parlay and provide recommendations."""
        try:
            analysis = {
                'overall_rating': 0,
                'risk_level': 'Medium',
                'expected_value': 0.0,
                'legs_analysis': [],
                'recommendations': [],
                'error': None
            }

            # Analyze each leg
            total_strength = 0
            risk_factors = []
            
            for leg in parlay.legs:
                try:
                    leg_analysis = await self._analyze_leg(leg)
                    analysis['legs_analysis'].append(leg_analysis)
                    total_strength += leg_analysis['strength']
                    risk_factors.extend(leg_analysis.get('risk_factors', []))
                except Exception as e:
                    analysis['legs_analysis'].append({
                        'team': leg.team,
                        'strength': 5,
                        'confidence': 'low',
                        'error': str(e)
                    })
                    risk_factors.append(f"Error analyzing {leg.team}: {str(e)}")

            # Calculate overall metrics
            num_legs = len(parlay.legs)
            if num_legs > 0:
                avg_strength = total_strength / num_legs
                analysis['overall_rating'] = round(avg_strength)
                
                # Calculate risk level
                analysis['risk_level'] = self._calculate_risk_level(
                    avg_strength, 
                    num_legs,
                    len(risk_factors)
                )
                
                # Calculate expected value
                analysis['expected_value'] = self._calculate_expected_value(
                    analysis['legs_analysis'],
                    parlay.stake,
                    parlay.total_odds
                )
                
                # Generate recommendations
                analysis['recommendations'] = self._generate_recommendations(
                    analysis['overall_rating'],
                    analysis['risk_level'],
                    analysis['expected_value'],
                    num_legs,
                    risk_factors
                )

            return analysis
            
        except Exception as e:
            return {
                'error': f"Error analyzing parlay: {str(e)}",
                'overall_rating': 0,
                'risk_level': 'Unknown',
                'expected_value': 0.0,
                'legs_analysis': [],
                'recommendations': ['Unable to analyze parlay due to error']
            }

    async def _analyze_leg(self, leg: BetLeg) -> Dict:
        """Analyze a single leg of the parlay."""
        analysis = {
            'team': leg.team,
            'bet_type': leg.bet_type,
            'odds': leg.odds,
            'strength': 5,  # Default middle rating
            'confidence': 'medium',
            'factors': [],
            'risk_factors': []
        }
        
        try:
            # Get team data if available
            if self.sports_api and leg.team:
                team_data = await self.sports_api.search_team(leg.team)
                if team_data:
                    analysis['factors'].append(f"Found team data for {leg.team}")
                else:
                    analysis['risk_factors'].append(f"No team data found for {leg.team}")

            # Analyze based on bet type
            if leg.bet_type == 'player_prop':
                analysis.update(self._analyze_player_prop(leg))
            elif leg.bet_type == 'spread':
                analysis.update(self._analyze_spread(leg))
            elif leg.bet_type == 'moneyline':
                analysis.update(self._analyze_moneyline(leg))
            elif leg.bet_type == 'total':
                analysis.update(self._analyze_total(leg))
            
            # Adjust strength based on odds
            odds_adjustment = self._calculate_odds_adjustment(leg.odds)
            analysis['strength'] = min(max(analysis['strength'] + odds_adjustment, 1), 10)
            
            # Update confidence based on risk factors
            if len(analysis['risk_factors']) > 2:
                analysis['confidence'] = 'low'
            elif len(analysis['risk_factors']) == 0 and analysis['strength'] >= 7:
                analysis['confidence'] = 'high'
                
        except Exception as e:
            analysis['risk_factors'].append(f"Error in analysis: {str(e)}")
            analysis['confidence'] = 'low'
            
        return analysis

    def _analyze_player_prop(self, leg: BetLeg) -> Dict:
        """Analyze a player prop bet."""
        analysis = {
            'factors': [],
            'risk_factors': []
        }
        
        if not leg.player:
            analysis['risk_factors'].append("No player specified")
            return analysis
            
        if not leg.prop_type or not leg.prop_value:
            analysis['risk_factors'].append("Incomplete prop details")
            return analysis
            
        # Add basic analysis
        analysis['factors'].append(f"Player prop: {leg.player} {leg.prop_type} {leg.prop_value}")
        
        # Assess odds value
        if leg.odds > 2.0:  # High odds
            analysis['risk_factors'].append("High odds suggest lower probability")
        
        return analysis

    def _analyze_spread(self, leg: BetLeg) -> Dict:
        """Analyze a spread bet."""
        analysis = {
            'factors': [],
            'risk_factors': []
        }
        
        if not leg.points:
            analysis['risk_factors'].append("No spread value specified")
            return analysis
            
        # Analyze spread value
        if abs(leg.points) > 10:
            analysis['risk_factors'].append("Large spread increases variance")
        elif abs(leg.points) < 3:
            analysis['factors'].append("Close spread suggests competitive matchup")
            
        return analysis

    def _analyze_moneyline(self, leg: BetLeg) -> Dict:
        """Analyze a moneyline bet."""
        analysis = {
            'factors': [],
            'risk_factors': []
        }
        
        # Analyze based on odds
        if leg.odds > 3.0:
            analysis['risk_factors'].append("High underdog odds")
        elif leg.odds < 1.2:
            analysis['risk_factors'].append("Very low favorite odds")
        else:
            analysis['factors'].append("Reasonable odds range")
            
        return analysis

    def _analyze_total(self, leg: BetLeg) -> Dict:
        """Analyze a totals bet."""
        analysis = {
            'factors': [],
            'risk_factors': []
        }
        
        if not leg.points:
            analysis['risk_factors'].append("No total points specified")
            return analysis
            
        # Basic total analysis
        analysis['factors'].append(f"Total points line: {leg.points}")
        
        return analysis

    def _calculate_odds_adjustment(self, odds: float) -> int:
        """Calculate strength adjustment based on odds."""
        if odds <= 0:
            return 0
        elif odds < 1.5:
            return 1  # Favorite
        elif odds > 2.5:
            return -1  # Underdog
        return 0

    def _calculate_risk_level(self, avg_strength: float, num_legs: int, num_risk_factors: int) -> str:
        """Calculate risk level based on multiple factors."""
        base_risk = 'Medium'
        
        # Adjust for number of legs
        if num_legs >= 4:
            base_risk = 'High'
        elif num_legs <= 2:
            base_risk = 'Low'
            
        # Adjust for strength
        if avg_strength >= 7:
            base_risk = f'{base_risk}-Low'
        elif avg_strength <= 4:
            base_risk = f'{base_risk}-High'
            
        # Adjust for risk factors
        if num_risk_factors >= num_legs:
            base_risk = 'High'
        elif num_risk_factors == 0 and avg_strength >= 6:
            base_risk = 'Low'
            
        return base_risk

    def _calculate_expected_value(self, legs_analysis: List[Dict], stake: float, total_odds: float) -> float:
        """Calculate expected value of the parlay."""
        try:
            # Calculate probability of winning based on strength ratings
            prob_winning = 1.0
            for leg in legs_analysis:
                leg_prob = leg['strength'] / 10.0  # Convert strength to probability
                prob_winning *= leg_prob
                
            # Calculate potential payout
            potential_payout = stake * total_odds
                
            # Calculate EV
            ev = (prob_winning * potential_payout) - stake
            return round(ev / stake * 100, 2)  # Return as percentage
            
        except Exception:
            return 0.0

    def _generate_recommendations(
        self,
        rating: int,
        risk_level: str,
        ev: float,
        num_legs: int,
        risk_factors: List[str]
    ) -> List[str]:
        """Generate betting recommendations."""
        recommendations = []
        
        # EV-based recommendations
        if ev > 10:
            recommendations.append("✅ Strong positive expected value")
        elif ev > 5:
            recommendations.append("✅ Positive expected value")
        elif ev < -10:
            recommendations.append("❌ Strong negative expected value")
        elif ev < -5:
            recommendations.append("❌ Negative expected value")
        
        # Number of legs recommendations
        if num_legs > 4:
            recommendations.append("⚠️ High number of legs increases risk")
        elif num_legs > 6:
            recommendations.append("🛑 Very high number of legs - consider splitting into multiple bets")
        
        # Risk level recommendations
        if 'High' in risk_level:
            recommendations.append("🎲 High risk - consider reducing stake")
        elif risk_level == 'Low':
            recommendations.append("✅ Low risk profile")
        
        # Rating-based recommendations
        if rating <= 3:
            recommendations.append("❌ Very low confidence - consider skipping")
        elif rating <= 5:
            recommendations.append("⚠️ Low confidence - proceed with caution")
        elif rating >= 8:
            recommendations.append("✅ High confidence in selections")
        
        # Risk factor recommendations
        if risk_factors:
            if len(risk_factors) >= num_legs:
                recommendations.append("🛑 Multiple risk factors identified - strongly consider revising")
            else:
                recommendations.append(f"⚠️ {len(risk_factors)} risk factors identified")
        
        return recommendations 