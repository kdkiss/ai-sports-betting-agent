# Sports Betting Analysis System

A comprehensive AI-powered sports betting analysis system that combines traditional statistics, web insights, and AI predictions to provide detailed betting recommendations.

## Features

### Multi-Sport Analysis
- NFL, NBA, UFC betting analysis
- Player props and game analysis
- Multi-sport parlay evaluation
- Cross-sport correlation detection

### AI-Powered Analysis
- DeepSeek AI integration for predictions
- Web scraping for latest insights
- Sentiment analysis of news and trends
- Risk assessment and value detection

### Advanced Analytics
- Expected value calculations
- Correlation analysis
- Risk-adjusted metrics
- Portfolio optimization

## Setup

### Prerequisites
- Python 3.8+
- API keys for:
  - DeepSeek API
  - Sports Data API
  - Weather API
  - Odds API

### Installation
```bash
# Clone the repository
git clone [repository-url]
cd sports-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration
Create a `.env` file with the following:
```
DEEPSEEK_API_KEY=your_deepseek_api_key
SPORTS_DATA_API_KEY=your_sports_data_api_key
WEATHER_API_KEY=your_weather_api_key
ODDS_API_KEY=your_odds_api_key
```

## Usage

### Basic Analysis
```python
from src.coordinator.sports_betting_coordinator import SportsBettingCoordinator

coordinator = SportsBettingCoordinator()

# Analyze a single bet
analysis = await coordinator.analyze_bet(
    "NFL Patriots vs Bills under 47.5"
)

# Analyze a parlay
parlay_analysis = await coordinator.analyze_bet(
    """
    NFL: Patriots vs Bills under 47.5
    NBA: Lakers -5.5 vs Warriors
    UFC: Jon Jones by KO/TKO
    """
)
```

### Understanding Results
The analysis includes:
- Overall recommendation
- Confidence level
- Expected value
- Risk assessment
- Key factors
- News insights
- Expert opinions
- AI predictions

### Response Format
```json
{
    "recommendation": "Consider",
    "confidence": 0.75,
    "expected_value": 0.15,
    "risk_assessment": "Medium",
    "key_factors": [
        "Strong historical trend",
        "Weather impact likely",
        "Key player injury"
    ],
    "news_summary": [...],
    "expert_opinions": [...],
    "ai_insights": [...]
}
```

## System Architecture

### Components
1. **Sport Agents**
   - Sport-specific analysis
   - Historical data processing
   - Matchup evaluation

2. **Data Clients**
   - Sports data retrieval
   - Odds monitoring
   - Weather information
   - News and trends

3. **AI Integration**
   - DeepSeek API client
   - Natural language processing
   - Sentiment analysis
   - Pattern recognition

4. **Coordinator**
   - Request routing
   - Multi-source analysis
   - Correlation detection
   - Final recommendations

### Data Flow
1. User submits bet for analysis
2. System identifies sports and bet types
3. Relevant data is gathered from multiple sources
4. Sport-specific agents perform analysis
5. AI models provide predictions
6. Results are combined and enhanced
7. Final recommendation is generated

## Performance Optimization

### Caching
- API responses cached for 1 hour
- Weather data cached for 3 hours
- News and trends cached for 1 hour

### Parallel Processing
- Concurrent API calls
- Parallel sport analysis
- Asynchronous data gathering

### Rate Limiting
- API call throttling
- Request queuing
- Automatic retries

## Error Handling

### API Failures
- Automatic retries with exponential backoff
- Fallback to cached data
- Graceful degradation

### Data Quality
- Validation of input data
- Confidence adjustments for missing data
- Warning system for incomplete analysis

### System Health
- Request logging
- Error tracking
- Performance monitoring

## Best Practices

### Responsible Betting
- Risk warnings
- Bankroll management advice
- Correlation awareness
- Portfolio diversification

### Analysis Quality
- Multiple data sources
- Cross-validation
- Confidence thresholds
- Regular updates

## Maintenance

### Updates
- Daily sports data refresh
- Hourly odds monitoring
- Real-time news tracking

### Monitoring
- System health checks
- API status monitoring
- Performance metrics
- Error logging

## Support

### Common Issues
- API connection problems
- Rate limit exceeded
- Data inconsistencies
- Analysis timeout

### Troubleshooting
1. Check API status
2. Verify API keys
3. Clear cache if needed
4. Check system logs

## Contributing
- Fork the repository
- Create feature branch
- Submit pull request
- Follow coding standards

## License
[License Type] - See LICENSE file for details 