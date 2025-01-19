from typing import Dict, Any, List, Optional
from ..agents.sport_identifier import SportIdentifier
from ..agents.sports.nfl_agent import NFLBettingAgent
from ..agents.sports.nba_agent import NBABettingAgent
from ..agents.sports.ufc_agent import UFCBettingAgent
from ..data.sports_data_client import SportsDataClient
from ..data.odds_client import OddsClient
from ..data.weather_client import WeatherClient
from ..data.search_client import SearchClient
from ..data.deepseek_client import DeepSeekClient
from ..utils.query_handler import QueryHandler
from datetime import datetime

class SportsBettingCoordinator:
    """Coordinates sports betting analysis across different sports and data sources."""
    
    def __init__(self):
        # Initialize sport identifier
        self.identifier = SportIdentifier()
        
        # Initialize betting agents
        self.agents = {
            'NFL': NFLBettingAgent(),
            'NBA': NBABettingAgent(),
            'UFC': UFCBettingAgent()
            # Other agents will be added as implemented
        }
        
        # Initialize data clients
        self.sports_data = SportsDataClient()
        self.odds_data = OddsClient()
        self.weather_data = WeatherClient()
        self.search_client = SearchClient()
        self.deepseek = DeepSeekClient()
        
        # Initialize query handler
        self.query_handler = QueryHandler()
    
    async def process_user_input(self, text: str) -> Dict[str, Any]:
        """Process natural language user input."""
        # Parse the query
        query_info = self.query_handler.process_query(text)
        
        if query_info['type'] == 'capabilities':
            return query_info['response_handler'](query_info['params'])
            
        elif query_info['type'] == 'bet_suggestion':
            return await self.analyze_bet(query_info['params'][0])
            
        elif query_info['type'] == 'odds_query':
            return await self._get_odds_info(query_info['params'][0])
            
        elif query_info['type'] == 'player_stats':
            return await self._get_player_info(query_info['params'][0])
            
        elif query_info['type'] == 'weather_impact':
            return await self._get_weather_info(query_info['params'][0])
            
        elif query_info['type'] == 'correlation_check':
            return await self._check_correlation(
                query_info['params'][0],
                query_info['params'][1]
            )
            
        else:
            return query_info['response_handler'](query_info['params'])
    
    async def _get_odds_info(self, target: str) -> Dict[str, Any]:
        """Get detailed odds information."""
        sports = self.identifier.identify_sports(target)
        if not sports:
            return {'error': 'No supported sports identified in the query'}
            
        context = await self._gather_context(target, sports[0])
        odds_data = await self.odds_data.get_odds(sports[0], context)
        
        return {
            'type': 'odds_info',
            'target': target,
            'sport': sports[0],
            'odds': odds_data,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _get_player_info(self, player: str) -> Dict[str, Any]:
        """Get detailed player information."""
        context = {'player': player}
        
        # Get player stats
        stats = await self.sports_data.get_stats('player', context)
        
        # Get recent news
        news = await self.search_client.gather_insights({
            'player': player,
            'type': 'player_news'
        })
        
        # Get AI analysis
        ai_analysis = await self.deepseek.analyze_betting_context(
            context,
            'player_analysis'
        )
        
        return {
            'type': 'player_info',
            'player': player,
            'stats': stats,
            'news': news,
            'analysis': ai_analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _get_weather_info(self, target: str) -> Dict[str, Any]:
        """Get weather information and its impact."""
        sports = self.identifier.identify_sports(target)
        if not sports:
            return {'error': 'No supported sports identified in the query'}
            
        context = await self._gather_context(target, sports[0])
        
        if sports[0] not in ['NFL', 'MLB']:  # Indoor sports
            return {
                'type': 'weather_info',
                'message': f'Weather does not affect {sports[0]} games as they are played indoors.'
            }
            
        weather_data = await self.weather_data.get_forecast(context)
        impact_analysis = await self._analyze_weather_impact(weather_data, context)
        
        return {
            'type': 'weather_info',
            'target': target,
            'sport': sports[0],
            'weather': weather_data,
            'impact': impact_analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _check_correlation(
        self,
        item1: str,
        item2: str
    ) -> Dict[str, Any]:
        """Check correlation between two betting items."""
        # Get context for both items
        context1 = await self._gather_context(item1, None)
        context2 = await self._gather_context(item2, None)
        
        # Analyze correlation
        correlation = self._analyze_cross_sport_correlation(
            [{'analysis': context1}, {'analysis': context2}],
            []  # No web insights needed for correlation check
        )
        
        return {
            'type': 'correlation_info',
            'items': [item1, item2],
            'correlation': correlation,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _analyze_weather_impact(
        self,
        weather_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze weather impact on the game."""
        impact_factors = []
        risk_level = 'low'
        
        # Check temperature
        temp = weather_data.get('temperature')
        if temp:
            if temp < 32:
                impact_factors.append('Freezing temperatures may affect player performance')
                risk_level = 'high'
            elif temp > 90:
                impact_factors.append('High temperatures may cause fatigue')
                risk_level = 'medium'
        
        # Check precipitation
        precip = weather_data.get('precipitation')
        if precip and precip > 0.1:
            impact_factors.append('Precipitation may affect ball handling')
            risk_level = 'high'
        
        # Check wind
        wind = weather_data.get('wind_speed')
        if wind and wind > 15:
            impact_factors.append('High winds may affect passing/kicking game')
            risk_level = 'high'
        
        return {
            'risk_level': risk_level,
            'impact_factors': impact_factors,
            'historical_performance': await self._get_weather_history(context)
        }
    
    async def _get_weather_history(
        self,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get historical performance under similar weather conditions."""
        # This would be implemented to fetch historical data
        # For now, return placeholder
        return []
    
    async def analyze_bet(self, text: str) -> Dict[str, Any]:
        """Analyze a betting opportunity."""
        # Identify sports in the text
        sports = self.identifier.identify_sports(text)
        
        if not sports:
            return {'error': 'No supported sports identified in the text'}
            
        if len(sports) > 1:
            return await self._analyze_multi_sport_parlay(text, sports)
            
        sport = sports[0]
        if sport not in self.agents:
            return {'error': f'No agent available for {sport}'}
            
        # Get relevant data
        context = await self._gather_context(text, sport)
        
        # Get web insights
        context['web_insights'] = await self.search_client.gather_insights(context)
        
        # Get DeepSeek analysis
        context['ai_analysis'] = await self.deepseek.analyze_betting_context(
            context,
            'game_analysis' if 'player' not in context else 'player_props'
        )
        
        # Analyze using appropriate agent
        analysis = await self.agents[sport].analyze(context)
        
        # Enhance analysis with web insights and AI analysis
        return self._enhance_analysis(analysis, context)
    
    async def _analyze_multi_sport_parlay(self, text: str, sports: List[str]) -> Dict[str, Any]:
        """Analyze a parlay involving multiple sports."""
        analyses = []
        web_insights = []
        ai_analyses = []
        
        for sport in sports:
            if sport in self.agents:
                context = await self._gather_context(text, sport)
                # Get web insights for each leg
                context['web_insights'] = await self.search_client.gather_insights(context)
                web_insights.append(context['web_insights'])
                
                # Get DeepSeek analysis for each leg
                context['ai_analysis'] = await self.deepseek.analyze_betting_context(
                    context,
                    'game_analysis' if 'player' not in context else 'player_props'
                )
                ai_analyses.append(context['ai_analysis'])
                
                analysis = await self.agents[sport].analyze(context)
                analyses.append({
                    'sport': sport,
                    'analysis': self._enhance_analysis(
                        analysis,
                        context
                    )
                })
        
        # Get parlay-specific AI analysis
        parlay_context = {
            'analyses': analyses,
            'web_insights': web_insights,
            'ai_analyses': ai_analyses
        }
        parlay_ai_analysis = await self.deepseek.analyze_betting_context(
            parlay_context,
            'parlay'
        )
        
        correlation = self._analyze_cross_sport_correlation(analyses, web_insights)
        recommendation = self._generate_parlay_recommendation(
            analyses,
            correlation,
            parlay_ai_analysis
        )
        
        return {
            'type': 'multi_sport_parlay',
            'sports_involved': sports,
            'individual_analyses': analyses,
            'correlation_analysis': correlation,
            'ai_analysis': parlay_ai_analysis,
            'overall_recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _gather_context(self, text: str, sport: str) -> Dict[str, Any]:
        """Gather all relevant context data for analysis."""
        context = self.identifier.get_sport_specific_context(text, sport)
        
        # Enrich context with additional data
        context['odds'] = await self.odds_data.get_odds(sport, context)
        context['stats'] = await self.sports_data.get_stats(sport, context)
        
        if sport in ['NFL', 'MLB']:  # Outdoor sports
            context['weather'] = await self.weather_data.get_forecast(context)
            
        return context
    
    def _analyze_cross_sport_correlation(
        self,
        analyses: List[Dict[str, Any]],
        web_insights: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze correlation between different sports in a parlay."""
        correlation_factors = []
        warnings = []
        independence_score = 1.0
        
        # Check for same-day games
        game_times = {}
        for analysis in analyses:
            sport = analysis['sport']
            if 'game_time' in analysis['analysis']:
                game_times[sport] = analysis['analysis']['game_time']
        
        if len(game_times) > 1:
            same_day_games = self._check_same_day_games(game_times)
            if same_day_games:
                correlation_factors.append({
                    'type': 'timing',
                    'description': 'Multiple games on same day',
                    'impact': 'moderate'
                })
                independence_score *= 0.9
        
        # Check for related markets
        for i, analysis1 in enumerate(analyses):
            for analysis2 in analyses[i+1:]:
                market_correlation = self._check_market_correlation(
                    analysis1['analysis'],
                    analysis2['analysis']
                )
                if market_correlation:
                    correlation_factors.append(market_correlation)
                    independence_score *= 0.8
                    warnings.append(
                        f"Correlated markets found between {analysis1['sport']} "
                        f"and {analysis2['sport']}: {market_correlation['description']}"
                    )
        
        # Check for shared external factors
        shared_factors = self._identify_shared_factors(analyses)
        for factor in shared_factors:
            correlation_factors.append(factor)
            independence_score *= 0.95
            
        # Analyze web insights for correlations
        insight_correlations = self._analyze_insight_correlations(web_insights)
        correlation_factors.extend(insight_correlations['factors'])
        warnings.extend(insight_correlations['warnings'])
        independence_score *= insight_correlations['score']
        
        return {
            'correlation_factors': correlation_factors,
            'independence_score': independence_score,
            'warnings': warnings,
            'correlation_level': (
                'High' if independence_score < 0.7
                else 'Medium' if independence_score < 0.9
                else 'Low'
            )
        }
    
    def _analyze_insight_correlations(
        self,
        web_insights: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze correlations from web insights."""
        factors = []
        warnings = []
        correlation_score = 1.0
        
        # Check for shared key factors
        all_factors = []
        for insight in web_insights:
            all_factors.extend(insight.get('key_factors', []))
            
        # Count factor occurrences
        from collections import Counter
        factor_counts = Counter(all_factors)
        
        # Analyze shared factors
        for factor, count in factor_counts.items():
            if count > 1:
                factors.append({
                    'type': 'shared_factor',
                    'description': f'Multiple bets affected by: {factor}',
                    'impact': 'moderate'
                })
                correlation_score *= 0.95
                warnings.append(f"Common factor found: {factor}")
        
        # Check sentiment alignment
        sentiments = [
            insight.get('overall_sentiment', {}).get('interpretation')
            for insight in web_insights
        ]
        if len(set(sentiments)) == 1 and sentiments[0] != 'Neutral':
            factors.append({
                'type': 'sentiment',
                'description': f'All bets show {sentiments[0].lower()} sentiment',
                'impact': 'moderate'
            })
            correlation_score *= 0.95
        
        return {
            'factors': factors,
            'warnings': warnings,
            'score': correlation_score
        }
    
    def _enhance_analysis(
        self,
        analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance betting analysis with web insights and AI analysis."""
        # Add web insights to key factors
        if 'key_factors' in analysis:
            analysis['key_factors'].extend(
                context.get('web_insights', {}).get('key_factors', [])
            )
        
        # Combine with AI analysis
        ai_analysis = context.get('ai_analysis', {})
        if ai_analysis:
            # Adjust confidence based on AI confidence
            if 'confidence' in analysis and 'confidence_score' in ai_analysis:
                analysis['confidence'] = (
                    analysis['confidence'] + ai_analysis['confidence_score']
                ) / 2
            
            # Merge risk factors
            if 'risk_factors' in ai_analysis:
                analysis.setdefault('risk_factors', []).extend(
                    ai_analysis['risk_factors']
                )
            
            # Update recommendation if AI strongly disagrees
            if (
                'recommendation' in ai_analysis
                and ai_analysis.get('confidence_score', 0) > 0.8
                and ai_analysis['recommendation'] != analysis.get('recommendation')
            ):
                analysis['alternative_recommendation'] = {
                    'source': 'AI Analysis',
                    'recommendation': ai_analysis['recommendation'],
                    'confidence': ai_analysis.get('confidence_score'),
                    'reasoning': ai_analysis.get('key_factors', [])
                }
        
        # Add web insights
        web_insights = context.get('web_insights', {})
        if web_insights:
            analysis['news_summary'] = web_insights.get('news_summary', [])
            analysis['expert_opinions'] = web_insights.get('expert_opinions', [])
            analysis['injury_notes'] = web_insights.get('injury_notes', [])
            analysis['betting_trends'] = web_insights.get('betting_trends', [])
        
        return analysis
    
    def _check_same_day_games(self, game_times: Dict[str, str]) -> bool:
        """Check if multiple games are on the same day."""
        dates = set()
        for time_str in game_times.values():
            try:
                game_time = datetime.fromisoformat(time_str)
                dates.add(game_time.date())
            except (ValueError, TypeError):
                continue
        return len(dates) < len(game_times)
    
    def _check_market_correlation(
        self,
        analysis1: Dict[str, Any],
        analysis2: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check for correlations between betting markets."""
        # Example correlations to check:
        # - Over/under correlations across games
        # - Player props from same team/game
        # - Related stat categories
        
        market1 = analysis1.get('market_type')
        market2 = analysis2.get('market_type')
        
        if market1 == market2 == 'total':
            return {
                'type': 'market',
                'description': 'Multiple over/under bets',
                'impact': 'significant'
            }
            
        if 'player' in analysis1 and 'player' in analysis2:
            if analysis1['player'] == analysis2['player']:
                return {
                    'type': 'player',
                    'description': 'Multiple bets on same player',
                    'impact': 'high'
                }
                
        return None
    
    def _identify_shared_factors(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify factors that could affect multiple bets."""
        shared_factors = []
        
        # Check for weather impact across outdoor sports
        outdoor_games = [a for a in analyses if a['sport'] in ['NFL', 'MLB']]
        if len(outdoor_games) > 1:
            weather_impacts = [
                a['analysis'].get('weather', {}).get('impact')
                for a in outdoor_games
            ]
            if any(impact == 'negative' for impact in weather_impacts):
                shared_factors.append({
                    'type': 'weather',
                    'description': 'Multiple outdoor games affected by weather',
                    'impact': 'moderate'
                })
        
        return shared_factors
    
    def _generate_parlay_recommendation(
        self,
        analyses: List[Dict[str, Any]],
        correlation: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall recommendation for a multi-sport parlay."""
        if not analyses:
            return {
                'recommendation': 'Pass',
                'confidence': 0.0,
                'key_factors': ['No valid analyses available'],
                'risk_assessment': 'High'
            }
            
        # Calculate aggregate metrics
        total_ev = sum(a['analysis'].get('expected_value', 0) for a in analyses)
        avg_confidence = sum(
            a['analysis'].get('confidence', 0) for a in analyses
        ) / len(analyses)
        
        # Adjust for correlations
        independence_score = correlation.get('independence_score', 1.0)
        adjusted_ev = total_ev * independence_score
        adjusted_confidence = avg_confidence * independence_score
        
        # Consider AI analysis
        if ai_analysis and 'recommendation' in ai_analysis:
            ai_confidence = ai_analysis.get('confidence_score', 0)
            if ai_confidence > 0.8:
                # Heavily weight AI recommendation for high confidence predictions
                adjusted_confidence = (
                    adjusted_confidence + ai_confidence * 2
                ) / 3
        
        # Gather risk factors
        risk_factors = []
        for analysis in analyses:
            if 'risk_assessment' in analysis['analysis']:
                risk_factors.extend(
                    analysis['analysis']['risk_assessment'].get('factors', [])
                )
        
        # Add correlation warnings
        risk_factors.extend(correlation.get('warnings', []))
        
        # Add AI risk factors
        if ai_analysis and 'risk_factors' in ai_analysis:
            risk_factors.extend(ai_analysis['risk_factors'])
        
        # Make recommendation
        recommendation = 'Pass'
        if adjusted_ev > 0.1 and adjusted_confidence > 0.6 and len(risk_factors) < 3:
            recommendation = 'Consider'
            if adjusted_ev > 0.2 and adjusted_confidence > 0.7:
                recommendation = 'Strong Consider'
        
        # Override with AI recommendation if highly confident
        if (
            ai_analysis
            and ai_analysis.get('confidence_score', 0) > 0.9
            and 'recommendation' in ai_analysis
        ):
            recommendation = ai_analysis['recommendation']
        
        return {
            'recommendation': recommendation,
            'confidence': adjusted_confidence,
            'expected_value': adjusted_ev,
            'raw_ev': total_ev,
            'correlation_adjustment': independence_score,
            'key_factors': risk_factors,
            'risk_assessment': 'High' if len(risk_factors) > 2 else 'Medium',
            'ai_insights': ai_analysis.get('key_factors', []),
            'timestamp': datetime.now().isoformat()
        } 