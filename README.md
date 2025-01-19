![image](https://github.com/user-attachments/assets/0b8d0aef-f8ed-4dfe-9331-f826ba5b3f96)

# Sports Betting Analysis System

An AI-powered sports betting analysis system that uses advanced LLM technology to analyze betting slips and provide detailed recommendations for player props and parlays. Access the system through a convenient Telegram bot interface.

## Features

### Intelligent Bet Analysis
- Dynamic player and team identification
- Automated bet extraction from betting slips
- Smart validation of bet completeness
- Risk assessment and analysis

### Telegram Integration
- Easy-to-use bot interface
- Upload betting slip screenshots
- Receive instant analysis
- Interactive commands
- Real-time notifications
- User-friendly responses

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

## Security

### API Keys and Secrets
- Never commit API keys or secrets to version control
- Use environment variables for all sensitive data
- Keep `.env` file in your local environment only
- Use `.env.example` as a template (with placeholder values)

### Environment Variables
```bash
# .env.example - DO NOT add actual keys here
DEEPSEEK_API_KEY=your_deepseek_api_key
SPORTS_DATA_API_KEY=your_sports_data_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

### Best Practices
- Regularly rotate API keys
- Use strong, unique keys for each environment
- Monitor API usage for unauthorized access
- Implement rate limiting
- Keep dependencies updated

### Data Protection
- No sensitive data is stored locally
- All API communications use HTTPS
- Implement proper error handling to avoid data leaks
- Log files exclude sensitive information

## Setup

### Prerequisites
- Python 3.8+
- Tesseract OCR:
  - Windows: [Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - Linux: `sudo apt-get install tesseract-ocr`
  - Mac: `brew install tesseract`
- API keys for:
  - DeepSeek API
  - Sports Data API
  - Telegram Bot Token (get from @BotFather)

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
# Edit .env with your API keys and Tesseract path
```

### Configuration
Create a `.env` file with the following:
```
DEEPSEEK_API_KEY=your_deepseek_api_key
SPORTS_DATA_API_KEY=your_sports_data_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Tesseract Configuration
TESSERACT_PATH=/usr/bin/tesseract  # Linux/Mac
# TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows
```

### Tesseract Setup
1. Install Tesseract OCR using the instructions above for your OS
2. Verify installation:
   ```bash
   tesseract --version
   ```
3. Update the `TESSERACT_PATH` in your `.env` file to point to your Tesseract executable
4. For Windows users:
   - Add Tesseract installation directory to system PATH
   - Default path is usually `C:\Program Files\Tesseract-OCR`
   - Restart your terminal after installation

## Usage

### Telegram Bot
1. Start the bot:
   ```bash
   python run.py
   ```
2. Find the bot on Telegram using the username provided by @BotFather
3. Start a conversation with `/start`
4. Upload a betting slip screenshot or paste the text
5. Receive detailed analysis and recommendations

### Available Commands
- `/start` - Begin interaction with the bot
- `/help` - Show available commands
- `/analyze` - Analyze a betting slip (with image or text)
- `/settings` - Configure your preferences
- `/status` - Check system status

### Python API
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
