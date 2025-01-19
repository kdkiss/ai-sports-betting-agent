# Sports Betting Analysis System

An AI-powered sports betting analysis system that uses advanced LLM technology to analyze betting slips and provide detailed recommendations for player props and parlays.

## Features

### Intelligent Bet Analysis
- Dynamic player and team identification
- Automated bet extraction from betting slips
- Smart validation of bet completeness
- Risk assessment and analysis

### LLM Integration
- DeepSeek AI for bet analysis
- Intelligent player name correction
- Dynamic bet type recognition
- Confidence-based filtering

### Advanced Analytics
- Expected value calculations
- Risk assessment
- Historical performance analysis
- Statistical validation

## Setup

### Prerequisites
- Python 3.8+
- API keys for:
  - DeepSeek API
  - Sports Data API

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
```

## Usage

### Bet Analysis
```python
from src.services.bet_analyzer import BetAnalyzer

analyzer = BetAnalyzer()

# Analyze betting slip
analysis = await analyzer.analyze_bets("""
    J. Hurts o/u 250.5 passing yards -110
    C. Kupp anytime TD +140
    T. Kelce o/u 70.5 receiving yards -115
""")
```

### Understanding Results
The analysis includes:
- Identified players and teams
- Validated bet components
- Risk assessment
- Statistical analysis
- Historical performance

### Response Format
```json
{
    "bets": [
        {
            "player": "Jalen Hurts",
            "team": "Philadelphia Eagles",
            "bet_type": "passing_yards",
            "line": 250.5,
            "odds": -110,
            "analysis": {
                "confidence": "high",
                "historical_avg": 245.3,
                "recommendation": "consider"
            }
        }
    ],
    "overall_analysis": {
        "complete_legs": 3,
        "risk_level": "medium",
        "recommendations": [...]
    }
}
```

## System Architecture

### Components
1. **Bet Analyzer**
   - LLM-based bet extraction
   - Player identification
   - Validation logic
   - Risk analysis

2. **Data Clients**
   - Sports statistics
   - Historical performance
   - Player data

3. **LLM Integration**
   - DeepSeek API client
   - Intelligent text processing
   - Confidence-based filtering

### Data Flow
1. User submits betting slip
2. System extracts and validates bets
3. Players and teams are identified
4. Statistical analysis is performed
5. Final recommendations generated

## Error Handling

### Validation
- Incomplete bet filtering
- Player name verification
- Line and odds validation
- Data quality checks

### System Health
- Request logging
- Error tracking
- Performance monitoring

## Best Practices

### Analysis Quality
- Confidence thresholds for player identification
- Complete information requirements
- Statistical validation
- Regular updates

## Support

### Common Issues
- OCR text quality
- Incomplete bet information
- Player identification accuracy
- API connection issues

### Troubleshooting
1. Check bet slip text quality
2. Verify all bet components
3. Check API status
4. Review system logs

## Contributing
- Fork the repository
- Create feature branch
- Submit pull request
- Follow coding standards

## License
[License Type] - See LICENSE file for details 