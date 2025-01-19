from typing import Dict, Any, List
from .base_agent import BaseAgent

class BankrollManagementAgent(BaseAgent):
    """Agent responsible for bankroll management and bet sizing."""

    def __init__(self, llm):
        """Initialize the agent with LLM service."""
        super().__init__(llm=llm)

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bet sizing and bankroll management."""
        response = await self._get_llm_analysis(context)
        return self._parse_response(response)

    def _create_prompt(self, context: Dict[str, Any]) -> str:
        """Create a detailed prompt for bankroll management analysis."""
        return f"""Analyze this betting opportunity for optimal bankroll management:

User Profile:
- Current Bankroll: ${context['bankroll']}
- Risk Tolerance: {context['risk_tolerance']}
- Betting History: Win Rate {context.get('win_rate', 'N/A')}%, ROI {context.get('roi', 'N/A')}%
- Current Open Bets: {context.get('open_bets', [])}

Bet Details:
- Type: {context['bet_type']}
- Odds: {context['odds']}
- Potential Payout: ${context['potential_payout']}
- Confidence Level: {context['confidence']}/10
- Value Rating: {context.get('value_rating', 'N/A')}/10

Risk Assessment:
- Market Volatility: {context.get('market_volatility', 'N/A')}
- Correlation with Open Bets: {context.get('correlation', 'N/A')}
- Expected Value: {context.get('expected_value', 'N/A')}

Historical Performance:
- Similar Bets ROI: {context.get('similar_bets_roi', 'N/A')}%
- Category Performance: {context.get('category_performance', 'N/A')}
- Variance Stats: {context.get('variance_stats', 'N/A')}

Analyze this opportunity considering:
1. Kelly Criterion calculation
2. Portfolio theory principles
3. Risk of ruin
4. Correlation with existing positions
5. Bankroll growth objectives
6. Drawdown management
7. Long-term sustainability

Provide comprehensive bankroll management advice including:
1. Recommended bet size (units and dollars)
2. Maximum exposure guidelines
3. Risk management strategies
4. Position sizing rationale
5. Hedging recommendations
6. Bankroll allocation strategy
7. Stop-loss levels
"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured bankroll management advice."""
        # This is a placeholder implementation
        return {
            'bet_sizing': {
                'recommended_units': 2,
                'recommended_amount': 200,
                'max_bet': 500,
                'kelly_fraction': 0.3
            },
            'risk_management': {
                'max_portfolio_exposure': '15%',
                'stop_loss_level': '-25%',
                'hedging_threshold': '50% profit',
                'risk_of_ruin': 'Low'
            },
            'bankroll_strategy': {
                'current_allocation': {
                    'high_confidence': '40%',
                    'medium_confidence': '35%',
                    'speculative': '25%'
                },
                'recommended_changes': [
                    'Increase high confidence allocation',
                    'Reduce speculative positions',
                    'Build cash reserve'
                ]
            },
            'position_management': {
                'entry_strategy': 'Scale in 50% now, 50% on pullback',
                'exit_strategy': 'Scale out at +50% and +100%',
                'hedge_recommendations': [
                    'Consider opposite side at +75%',
                    'Use correlated markets for hedging'
                ]
            },
            'warnings': [
                'High correlation with existing positions',
                'Approaching maximum category exposure',
                'Consider reducing position size'
            ],
            'action_items': [
                'Set stop loss at -25%',
                'Monitor correlation with open positions',
                'Review portfolio balance weekly',
                'Adjust position size based on volatility'
            ]
        } 