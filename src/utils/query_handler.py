from typing import Dict, Any, List, Optional
import re
from datetime import datetime

class QueryHandler:
    """Handles natural language queries and commands from users."""
    
    def __init__(self):
        # Define query patterns
        self.patterns = {
            'capabilities': [
                r'what (?:can|could) you do',
                r'(?:show|tell|list) (?:me )?(?:your )?(?:features|capabilities)',
                r'help',
                r'how (?:do|can) I use (?:you|this)',
                r'what (?:are|is) your (?:features|capabilities)'
            ],
            'bet_suggestion': [
                r'(?:should|could|can|would) I bet (?:on )?(.+)',
                r'(?:what|how) (?:do|would) you think about (?:betting on )?(.+)',
                r'analyze (?:this )?(?:bet|parlay)?(?: on )?(.+)',
                r'(?:is|are) (.+) a good bet',
                r'what(?:\'s| is) your (?:take|opinion|thought) on (.+)'
            ],
            'odds_query': [
                r'what (?:are|is) the odds (?:for|on) (.+)',
                r'(?:show|get|find) (?:me )?odds (?:for|on) (.+)',
                r'odds (?:for|on) (.+)'
            ],
            'player_stats': [
                r'(?:how is|how\'s) (.+) (?:playing|performing|doing)',
                r'(?:show|get|find) (?:me )?stats (?:for|on) (.+)',
                r'(?:what are|what\'s) (.+)(?:\'s)? stats'
            ],
            'weather_impact': [
                r'(?:how|what)(?:\'s| is) the weather (?:for|in) (.+)',
                r'will weather (?:affect|impact) (.+)',
                r'weather (?:report|forecast) (?:for|in) (.+)'
            ],
            'correlation_check': [
                r'(?:are|is) (.+) (?:and|&) (.+) correlated',
                r'correlation between (.+) and (.+)',
                r'(?:how|are) (?:do|does) (.+) affect (.+)'
            ]
        }
        
        # Compile patterns
        self.compiled_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) 
                      for pattern in patterns]
            for category, patterns in self.patterns.items()
        }
        
        # Define response templates
        self.responses = {
            'capabilities': self._get_capabilities_response,
            'bet_suggestion': self._get_bet_suggestion_response,
            'odds_query': self._get_odds_response,
            'player_stats': self._get_player_stats_response,
            'weather_impact': self._get_weather_impact_response,
            'correlation_check': self._get_correlation_response
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query and determine the appropriate response type."""
        # Check each category of patterns
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(query)
                if match:
                    # Get response handler
                    response_handler = self.responses[category]
                    
                    # Extract parameters from match groups
                    params = match.groups() if match.groups() else []
                    
                    return {
                        'type': category,
                        'query': query,
                        'params': params,
                        'timestamp': datetime.now().isoformat(),
                        'response_handler': response_handler
                    }
        
        # If no pattern matches, return default response
        return {
            'type': 'unknown',
            'query': query,
            'params': [],
            'timestamp': datetime.now().isoformat(),
            'response_handler': self._get_default_response
        }
    
    def _get_capabilities_response(self, params: List[str]) -> Dict[str, Any]:
        """Generate response for capabilities query."""
        return {
            'type': 'capabilities',
            'content': {
                'features': [
                    'Analyze single bets and parlays',
                    'Check player statistics and performance',
                    'Monitor odds and line movements',
                    'Assess weather impact on games',
                    'Detect correlations between bets',
                    'Provide AI-powered predictions',
                    'Track news and expert opinions',
                    'Calculate expected value and risk'
                ],
                'supported_sports': [
                    'NFL (Football)',
                    'NBA (Basketball)',
                    'UFC (Mixed Martial Arts)'
                ],
                'analysis_types': [
                    'Game analysis',
                    'Player props',
                    'Team props',
                    'Parlay analysis',
                    'Value betting opportunities'
                ]
            }
        }
    
    def _get_bet_suggestion_response(self, params: List[str]) -> Dict[str, Any]:
        """Generate response for bet suggestion query."""
        bet_text = params[0] if params else ''
        return {
            'type': 'analysis_request',
            'content': {
                'text': bet_text,
                'analysis_type': 'comprehensive',
                'include_factors': [
                    'odds',
                    'weather',
                    'injuries',
                    'trends',
                    'news'
                ]
            }
        }
    
    def _get_odds_response(self, params: List[str]) -> Dict[str, Any]:
        """Generate response for odds query."""
        target = params[0] if params else ''
        return {
            'type': 'odds_request',
            'content': {
                'target': target,
                'include': [
                    'current_odds',
                    'line_movement',
                    'market_sentiment'
                ]
            }
        }
    
    def _get_player_stats_response(self, params: List[str]) -> Dict[str, Any]:
        """Generate response for player stats query."""
        player = params[0] if params else ''
        return {
            'type': 'stats_request',
            'content': {
                'player': player,
                'include': [
                    'recent_performance',
                    'season_stats',
                    'matchup_history',
                    'situational_stats'
                ]
            }
        }
    
    def _get_weather_impact_response(self, params: List[str]) -> Dict[str, Any]:
        """Generate response for weather impact query."""
        target = params[0] if params else ''
        return {
            'type': 'weather_request',
            'content': {
                'target': target,
                'include': [
                    'forecast',
                    'impact_analysis',
                    'historical_performance'
                ]
            }
        }
    
    def _get_correlation_response(self, params: List[str]) -> Dict[str, Any]:
        """Generate response for correlation check query."""
        return {
            'type': 'correlation_request',
            'content': {
                'items': list(params),
                'include': [
                    'direct_correlation',
                    'shared_factors',
                    'historical_patterns'
                ]
            }
        }
    
    def _get_default_response(self, params: List[str]) -> Dict[str, Any]:
        """Generate default response for unknown queries."""
        return {
            'type': 'clarification_request',
            'content': {
                'message': 'I\'m not sure what you\'re asking. Could you please:',
                'suggestions': [
                    'Ask about a specific bet or parlay',
                    'Check odds for a game',
                    'Look up player statistics',
                    'Check weather impact',
                    'Ask about my capabilities'
                ]
            }
        } 