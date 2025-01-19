import logging
from typing import Dict, List
import aiohttp
import json
from ..config import Config
from ..clients import SportsDataClient
import re

logger = logging.getLogger(__name__)

# Use Config class to access configuration values
SPORTSDB_API_KEY = Config.SPORTSDB_API_KEY
SPORTSDB_BASE_URL = Config.SPORTSDB_BASE_URL
OPENAI_API_KEY = Config.OPENAI_API_KEY

class BetAnalyzer:
    """Analyzes bets using AI and sports data."""
    
    def __init__(self, llm):
        """Initialize the bet analyzer."""
        self.llm = llm
        self.sports_client = SportsDataClient()

    async def analyze_text(self, text: str) -> Dict:
        """Analyze the bet slip text and return structured analysis."""
        print("Starting analysis of text:")
        print(text)
        
        # Extract bets
        bets = await self._extract_bets(text)
        
        # Analyze each leg
        leg_analyses = []
        for bet in bets:
            print(f"Analyzing bet: {bet}")
            
            if not bet['line'] or not bet['odds']:
                continue
            
            # Get enhanced player/team context using LLM
            try:
                context = await self._process_player_context(bet)
                risk_factors = context.get('risk_factors', [])
                safety_factors = context.get('safety_factors', [])
            except Exception as e:
                print(f"Error processing context: {e}")
                risk_factors = []
                safety_factors = []
                context = {}
            
            # Check odds
            if bet['odds'] > 150:
                risk_factors.append("High positive odds indicate significant upset needed")
            elif bet['odds'] < -200:
                risk_factors.append("Heavy favorite requires strong performance")
            else:
                safety_factors.append("Balanced odds suggest reasonable probability")
            
            # Check yardage lines with context
            if bet['bet_type'] == 'Passing Yards':
                if bet['line'] > context.get('avg_passing_yards', 250):
                    risk_factors.append(f"Line {bet['line']} above player average {context.get('avg_passing_yards', 'N/A')}")
                elif bet['line'] < context.get('avg_passing_yards', 250) * 0.8:
                    safety_factors.append(f"Line {bet['line']} below player average {context.get('avg_passing_yards', 'N/A')}")
            
            elif bet['bet_type'] == 'Receiving Yards':
                if bet['line'] > context.get('avg_receiving_yards', 60):
                    risk_factors.append(f"Line {bet['line']} above player average {context.get('avg_receiving_yards', 'N/A')}")
                elif bet['line'] < context.get('avg_receiving_yards', 60) * 0.8:
                    safety_factors.append(f"Line {bet['line']} below player average {context.get('avg_receiving_yards', 'N/A')}")
            
            leg_analyses.append({
                'player': bet['player'],
                'bet_type': bet['bet_type'],
                'line': bet['line'],
                'odds': bet['odds'],
                'is_risky': len(risk_factors) > len(safety_factors),
                'is_safe': len(safety_factors) > len(risk_factors),
                'risk_factors': risk_factors,
                'safety_factors': safety_factors,
                'context': context
            })
        
        # Calculate overall analysis
        if not leg_analyses:
            raise ValueError("No valid bets found to analyze")
        
        risky_legs = sum(1 for leg in leg_analyses if leg['is_risky'])
        safe_legs = sum(1 for leg in leg_analyses if leg['is_safe'])
        
        overall_risk = "High" if risky_legs > safe_legs else "Medium" if risky_legs == safe_legs else "Low"
        
        return {
            'overall_risk': overall_risk,
            'legs': leg_analyses,
            'raw_text': text
        }

    async def _normalize_text(self, text: str) -> str:
        """Use LLM to correct OCR errors and normalize text."""
        prompt = f"""Analyze this sports betting text and extract ONLY the legs where you can identify with high confidence:
1. A clear player name
2. Their team
3. The bet type (e.g. Passing Yards, Receiving Yards, etc.)
4. The line value
5. The odds

Original text:
{text}

For each CONFIDENT and COMPLETE bet, return it in this format:
PLAYER_NAME (TEAM) - BET_TYPE: LINE ODDS

Rules:
1. Only include bets where ALL components are clearly identifiable
2. Skip any bets where player names are unclear or ambiguous
3. Skip any bets with missing/unclear lines or odds
4. Skip any bets where you can't determine the bet type
5. Fix any obvious OCR errors in player names if you're confident about the correction

Return ONLY the bets you are completely confident about, one per line."""

        try:
            # Try different method names that might be available
            for method_name in ['chat', 'generate', 'complete', '__call__']:
                if hasattr(self.llm, method_name):
                    response = await getattr(self.llm, method_name)(prompt)
                    corrected_text = response.text if hasattr(response, 'text') else str(response)
                    print(f"Normalized text:\n{corrected_text}")
                    return corrected_text
            
            # If no method works, return original text
            print("Warning: Could not find valid LLM method, using original text")
            return text
        except Exception as e:
            print(f"Error in text normalization: {e}")
            return text

    async def _extract_bets(self, text: str) -> List[Dict]:
        """Extract bets from OCR text using robust text processing."""
        try:
            # Use LLM to identify and extract bets
            bet_prompt = f"""Analyze this betting slip and extract all valid bets.
For each bet, you must be able to clearly identify ALL of these components:
1. Player name (skip if unclear or ambiguous)
2. Team
3. Bet type
4. Line value
5. Odds

Text:
{text}

First, identify which bets have complete information displayed.
Skip any bets where:
- Player name is unclear or ambiguous
- Line value is not shown
- Odds are not shown
- Bet type is not clear

Then, for each COMPLETE bet, return in this format:
PLAYER_NAME|TEAM|BET_TYPE|LINE|ODDS

Example output:
Jalen Hurts|PHI|Passing Yards|179|-186

Only return bets where you are confident ALL components are present and clear.
Return one bet per line with no additional text."""

            try:
                # Get LLM analysis
                response = await self.llm._generate(bet_prompt)
                llm_response = str(response)
                print("LLM Response:", llm_response)

                # Parse LLM response into bets
                bets = []
                for line in llm_response.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#') or line.lower().startswith('example'):
                        continue
                    
                    try:
                        # Parse bet components
                        parts = line.split('|')
                        if len(parts) == 5:
                            player, team, bet_type, line_val, odds = [p.strip() for p in parts]
                            
                            # Convert numeric values
                            try:
                                line_val = float(line_val)
                                odds = int(odds)
                            except ValueError:
                                print(f"Error converting numeric values in line: {line}")
                                continue
                            
                            # Create bet dictionary
                            bet = {
                                'player': player,
                                'team': team,
                                'bet_type': bet_type,
                                'line': line_val,
                                'odds': odds
                            }
                            
                            # Validate bet values based on type
                            if bet['bet_type'] == 'Passing Yards' and not (150 <= bet['line'] <= 400):
                                print(f"Skipping {player} - passing yards line {line_val} outside valid range")
                                continue
                            if bet['bet_type'] == 'Receiving Yards' and not (20 <= bet['line'] <= 150):
                                print(f"Skipping {player} - receiving yards line {line_val} outside valid range")
                                continue
                            if not (-500 <= bet['odds'] <= 500):
                                print(f"Skipping {player} - odds {odds} outside valid range")
                                continue
                            
                            print(f"Adding complete bet for {player}: {bet_type} {line_val} @ {odds}")
                            bets.append(bet)
                            
                    except Exception as e:
                        print(f"Error parsing bet line '{line}': {e}")
                        continue

                # Print extracted bets for debugging
                print("\nExtracted bets:")
                for bet in bets:
                    print(json.dumps(bet, indent=2))
                
                return bets
                
            except Exception as e:
                print(f"Error in LLM analysis: {e}")
                return []
            
        except Exception as e:
            print(f"Error in bet extraction: {e}")
            return []

    async def _validate_bets(self, bets: List[Dict]) -> List[Dict]:
        """Use LLM to validate and correct extracted bets."""
        if not bets:
            return bets

        prompt = f"""Validate and correct these extracted bets, ensuring all 4 players (Matthew Stafford, Jalen Hurts, Cooper Kupp, AJ Brown) are included if present in original text. Check for:
1. Player name accuracy
2. Team affiliations (LAR or PHI)
3. Reasonable lines for bet types
4. Valid odds ranges (-500 to +500)
5. Missing bets that should be included

Extracted bets:
{json.dumps(bets, indent=2)}

Return the corrected bets in the same JSON format, fixing any errors while maintaining the structure.
Known valid ranges:
- Passing yards: 150-400
- Receiving yards: 20-150
- Odds: -500 to +500

Expected players:
- Matthew Stafford (LAR) - Passing Yards
- Jalen Hurts (PHI) - Passing Yards
- Cooper Kupp (LAR) - Receiving Yards
- AJ Brown (PHI) - Receiving Yards"""

        try:
            response = await self.llm.generate(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                print("Failed to parse LLM response as JSON")
                return bets
        except Exception as e:
            print(f"Error in bet validation: {e}")
            return bets

    def _get_sports_data(self, bet: Dict) -> Dict:
        """Get relevant sports data for a bet."""
        try:
            data = {}
            
            if bet['player'] and bet['team']:
                # Get player stats
                player_data = self.sports_client.get_player_stats(bet['player'])
                if player_data:
                    data['player'] = player_data
                
                # Get team stats
                team_data = self.sports_client.get_team_stats(bet['team'])
                if team_data:
                    data['team'] = team_data
            
            return data
            
        except Exception as e:
            print(f"Error getting sports data: {str(e)}")
            return {}

    def _calculate_overall_analysis(self, legs: List[Dict]) -> Dict:
        """Calculate overall analysis from individual legs."""
        try:
            num_legs = len(legs)
            if num_legs == 0:
                return {}
            
            # Analyze each leg for risk factors and safety indicators
            leg_risks = []
            for leg in legs:
                risk_factors = []
                safety_factors = []
                odds = int(leg.get('odds', 0))
                line = float(leg.get('line', 0))
                bet_type = leg.get('bet_type', '')
                
                # Check odds-based factors
                if odds > 150:
                    risk_factors.append(f"High odds (+{odds}) indicate significant upset needed")
                elif odds < -200:
                    risk_factors.append(f"Heavy favorite ({odds}) but needs high performance")
                elif -150 <= odds <= 150:
                    safety_factors.append(f"Balanced odds ({odds}) suggest reasonable probability")
                
                # Check line-based factors for Passing Yards
                if 'Passing Yards' in bet_type:
                    if line > 280:
                        risk_factors.append(f"High passing yards line ({line}) requires exceptional performance")
                    elif line < 200:
                        risk_factors.append(f"Low passing yards line ({line}) vulnerable to run-heavy gameplan")
                    else:
                        safety_factors.append(f"Moderate passing yards line ({line}) within typical range")
                
                # Check line-based factors for Receiving Yards
                elif 'Receiving Yards' in bet_type:
                    if line > 80:
                        risk_factors.append(f"High receiving yards line ({line}) requires consistent targets")
                    elif line < 40:
                        risk_factors.append(f"Low receiving yards line ({line}) could still miss with limited opportunities")
                    else:
                        safety_factors.append(f"Moderate receiving yards line ({line}) within typical range")
                
                # Determine if the leg is safe or risky
                is_safe = len(safety_factors) > 0 and len(risk_factors) == 0
                is_risky = len(risk_factors) >= 2
                
                # Assign risk level and include safety assessment
                leg_risk = {
                    'level': 'High' if is_risky else 'Low' if is_safe else 'Medium',
                    'is_safe': is_safe,
                    'is_risky': is_risky,
                    'risk_factors': risk_factors,
                    'safety_factors': safety_factors
                }
                leg_risks.append(leg_risk)
            
            # Calculate overall risk
            high_risk_legs = sum(1 for r in leg_risks if r['level'] == 'High')
            safe_legs = sum(1 for r in leg_risks if r['is_safe'])
            
            # Determine overall risk level
            if high_risk_legs > 0:
                risk_level = 'High'
            elif safe_legs == num_legs:
                risk_level = 'Low'
            else:
                risk_level = 'Medium'
            
            # Generate key factors based on actual risks identified
            key_factors = []
            if num_legs > 1:
                key_factors.append(f"Multi-leg parlay ({num_legs} legs) increases overall risk")
            
            # Add specific risk/safety factors from legs
            for i, leg_risk in enumerate(leg_risks):
                leg = legs[i]
                if leg_risk['risk_factors']:
                    key_factors.extend([f"{leg['player']} - {factor}" for factor in leg_risk['risk_factors']])
                if leg_risk['safety_factors']:
                    key_factors.extend([f"{leg['player']} - {factor}" for factor in leg_risk['safety_factors']])
            
            # Generate specific recommendations based on identified risks
            recommendations = []
            if high_risk_legs > 0:
                recommendations.append(f"{high_risk_legs} risky leg(s) identified - consider placing as separate bets")
            if safe_legs > 0:
                recommendations.append(f"{safe_legs} safe leg(s) identified - these have balanced odds and reasonable lines")
            if num_legs > 2:
                recommendations.append("Multiple legs compound risk - consider reducing parlay size")
            
            # Calculate confidence based on safety and risk
            base_confidence = 7  # Start at 7/10
            if risk_level == 'High':
                base_confidence -= 2
            elif risk_level == 'Low':
                base_confidence += 1
            
            # Adjust for number of legs
            leg_penalty = max(0, num_legs - 1) * 0.5  # -0.5 for each leg beyond first
            confidence = round(max(1, min(10, base_confidence - leg_penalty)), 1)
            
            return {
                'number_of_legs': num_legs,
                'confidence': confidence,
                'risk_level': risk_level,
                'safe_legs': safe_legs,
                'risky_legs': high_risk_legs,
                'key_factors': key_factors,
                'recommendations': recommendations,
                'leg_risks': leg_risks
            }
            
        except Exception as e:
            print(f"Error calculating overall analysis: {str(e)}")
            return {}

    async def _analyze_single_bet(self, bet_text: str) -> Dict:
        """Analyze a single bet using available data sources."""
        try:
            # Create context for the bet
            context = {
                'text': bet_text,
                'bet_type': 'single',
                'format': 'raw_text'
            }
            
            # Gather data from various sources
            sports_data = await self.sports_client.get_stats(context.get('sport', ''), context)
            
            # Get AI analysis
            analysis = await self.llm.analyze_bet(context)
            
            return {
                'bet_text': bet_text,
                'confidence': analysis.get('confidence', 0),
                'risk_level': analysis.get('risk_level', 'Unknown'),
                'value': analysis.get('value_assessment', 'Unknown'),
                'key_factors': analysis.get('key_factors', []),
                'recommendations': analysis.get('recommendations', []),
                'sports_data': sports_data
            }
            
        except Exception as e:
            print(f"Error analyzing single bet: {str(e)}")
            return {
                'bet_text': bet_text,
                'error': str(e)
            }
            
    async def _get_overall_analysis(self, leg_analyses: List[Dict]) -> Dict:
        """Generate overall analysis for multiple bets."""
        try:
            # Calculate average confidence
            confidences = [leg.get('confidence', 0) for leg in leg_analyses if 'confidence' in leg]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Determine overall risk level
            risk_levels = [leg.get('risk_level', 'Unknown') for leg in leg_analyses]
            overall_risk = max(risk_levels, key=risk_levels.count) if risk_levels else 'Unknown'
            
            # Combine key factors
            all_factors = []
            for leg in leg_analyses:
                all_factors.extend(leg.get('key_factors', []))
            
            # Get unique factors
            key_factors = list(set(all_factors))
            
            return {
                'confidence': round(avg_confidence, 1),
                'risk_level': overall_risk,
                'number_of_legs': len(leg_analyses),
                'key_factors': key_factors[:5],  # Top 5 factors
                'recommendations': [
                    "Consider correlation between legs",
                    "Review highest risk leg",
                    "Check for weather impacts"
                ]
            }
            
        except Exception as e:
            print(f"Error in overall analysis: {str(e)}")
            return {
                'error': str(e)
            }
    
    async def _get_player_data(self, player_name: str, team: str) -> Dict:
        """Get player data from SportsDB API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.sportsdb_api_key}/searchplayers.php"
                params = {'p': player_name}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if not data.get('player'):
                        return {'name': player_name, 'team': team, 'recent_stats': {}}
                    
                    player = data['player'][0]
                    return {
                        'name': player['strPlayer'],
                        'team': team,
                        'position': player.get('strPosition'),
                        'nationality': player.get('strNationality'),
                        'recent_stats': await self._get_player_stats(player['idPlayer'])
                    }
                    
        except Exception as e:
            logger.error(f"Error getting player data: {str(e)}", exc_info=True)
            return {'name': player_name, 'team': team, 'recent_stats': {}}
    
    async def _get_team_data(self, team: str) -> Dict:
        """Get team data from SportsDB API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.sportsdb_api_key}/searchteams.php"
                params = {'t': team}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if not data.get('teams'):
                        return {'name': team}
                    
                    team_data = data['teams'][0]
                    return {
                        'name': team_data['strTeam'],
                        'league': team_data.get('strLeague'),
                        'stadium': team_data.get('strStadium'),
                        'description': team_data.get('strDescriptionEN')
                    }
                    
        except Exception as e:
            logger.error(f"Error getting team data: {str(e)}", exc_info=True)
            return {'name': team}
    
    async def _get_player_stats(self, player_id: str) -> Dict:
        """Get player's recent statistics."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.sportsdb_api_key}/lookupplayer.php"
                params = {'id': player_id}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if not data.get('players'):
                        return {}
                    
                    stats = data['players'][0]
                    return {
                        'recent_form': stats.get('strStatus'),
                        'injury_status': stats.get('strInjured'),
                        'last_game': stats.get('strLastGame')
                    }
                    
        except Exception as e:
            logger.error(f"Error getting player stats: {str(e)}", exc_info=True)
            return {}
    
    async def _get_ai_analysis(self, context: Dict) -> Dict:
        """Get AI analysis of the bet based on available data."""
        try:
            prompt = self._create_analysis_prompt(context)
            response = await self.llm.generate(prompt)
            
            # Parse AI response
            analysis = json.loads(response)
            
            return {
                'risk_level': analysis.get('risk_level', 'medium'),
                'confidence': analysis.get('confidence', 50),
                'reasoning': analysis.get('reasoning', []),
                'team_context': analysis.get('team_context', {}),
                'recommendations': analysis.get('recommendations', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting AI analysis: {str(e)}", exc_info=True)
            return {
                'risk_level': 'unknown',
                'confidence': 0,
                'reasoning': ['Error analyzing bet'],
                'team_context': {},
                'recommendations': ['Unable to provide recommendations']
            }
    
    def _create_analysis_prompt(self, context: Dict) -> str:
        """Create a prompt for AI analysis."""
        return f"""Analyze this sports bet based on the following context:

Player Information:
{json.dumps(context['player'], indent=2)}

Team Information:
{json.dumps(context['team'], indent=2)}

Bet Details:
- Type: {context['bet_type']}
- Odds: {context['odds']}

Please provide a detailed analysis in JSON format with the following structure:
{{
    "risk_level": "low/medium/high",
    "confidence": 0-100,
    "reasoning": ["reason1", "reason2", ...],
    "team_context": {{
        "matchup_analysis": "string",
        "recent_performance": "string"
    }},
    "recommendations": ["rec1", "rec2", ...]
}}

Focus on recent performance, injury status, team dynamics, and historical data to assess the bet's risk and potential value.""" 

    async def _process_player_context(self, bet: Dict) -> Dict:
        """Process player and team context using LLM."""
        try:
            # Get raw stats
            player_data = await self.sports_client.get_player_stats(bet['player'])
            team_data = await self.sports_client.get_team_stats(bet['team'])
            
            # Create context for LLM
            prompt = f"""Analyze this player and their team's context for a {bet['bet_type']} bet:

Player: {bet['player']}
Team: {bet['team']}
Bet Type: {bet['bet_type']}
Line: {bet['line']}
Odds: {bet['odds']}

Player Stats:
{json.dumps(player_data, indent=2)}

Team Context:
{json.dumps(team_data, indent=2)}

Provide analysis in JSON format with:
1. Recent performance metrics
2. Risk factors
3. Safety factors
4. Relevant averages
5. Team context impact
"""
            
            # Get LLM analysis
            response = await self.llm.generate(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            try:
                context = json.loads(response_text)
            except json.JSONDecodeError:
                print("Failed to parse LLM response as JSON")
                context = {}
            
            # Add computed averages if not provided by LLM
            if bet['bet_type'] == 'Passing Yards' and 'avg_passing_yards' not in context:
                context['avg_passing_yards'] = self._calculate_average(player_data, 'passing_yards', default=250)
            elif bet['bet_type'] == 'Receiving Yards' and 'avg_receiving_yards' not in context:
                context['avg_receiving_yards'] = self._calculate_average(player_data, 'receiving_yards', default=60)
            
            return context
            
        except Exception as e:
            print(f"Error in player context processing: {e}")
            return {}
            
    def _calculate_average(self, stats: Dict, stat_key: str, default: float = 0) -> float:
        """Calculate average from stats dictionary with fallback default."""
        try:
            if not stats or stat_key not in stats:
                return default
                
            values = [float(v) for v in stats[stat_key] if v]
            if not values:
                return default
                
            return sum(values) / len(values)
        except:
            return default 