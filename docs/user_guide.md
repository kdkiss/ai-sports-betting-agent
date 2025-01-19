# User Guide

## Getting Started

The Sports Betting Analysis System helps you analyze betting opportunities across multiple sports, with a focus on identifying value and managing risk in parlays.

### Supported Sports
- NFL (Football)
- NBA (Basketball)
- UFC (Mixed Martial Arts)

## Using the System

### Single Sport Bets

You can analyze individual bets by providing a description. The system understands natural language input:

```
"Chiefs -3.5 vs Raiders"
"Lakers team total over 115.5"
"Patrick Mahomes over 280.5 passing yards"
```

### Parlay Analysis

For parlays, list multiple bets. The system will analyze each leg and their relationships:

```
"Parlay:
Chiefs ML
Lakers -5.5
UFC Adesanya by KO"
```

### Player Props

When analyzing player props, include:
- Player name
- Stat type
- Line
- Optional: Game context

Examples:
```
"Steph Curry over 28.5 points vs Suns"
"Travis Kelce receiving yards over 75.5 in weather"
```

## Understanding Results

### Analysis Components

1. **Recommendation**
   - Pass: Not recommended
   - Consider: Potential value
   - Strong Consider: High confidence opportunity

2. **Expected Value**
   - Positive: Potentially profitable
   - Higher numbers indicate better value
   - Adjusted for correlations in parlays

3. **Risk Assessment**
   - Low: Standard risk level
   - Medium: Some concerns
   - High: Significant risk factors

4. **Key Factors**
   - Important considerations
   - Risk warnings
   - Correlation notes

### Sample Output

```json
{
    "recommendation": "Consider",
    "confidence": 0.75,
    "expected_value": 0.15,
    "risk_assessment": "Medium",
    "key_factors": [
        "Strong historical performance",
        "Favorable matchup",
        "Weather could be a factor"
    ]
}
```

## Best Practices

### Do's
1. Provide clear, specific bet descriptions
2. Include relevant context (weather, injuries, etc.)
3. Check all key factors before betting
4. Consider correlation warnings in parlays

### Don'ts
1. Ignore risk assessments
2. Overlook correlation warnings
3. Bet without checking current odds
4. Disregard weather impacts

## Advanced Features

### Weather Analysis
For outdoor sports (NFL), the system considers:
- Temperature
- Wind speed
- Precipitation
- Impact on different bet types

### Correlation Detection
The system identifies:
- Same-day games
- Related markets
- Common external factors
- Shared dependencies

### Value Calculation
Incorporates:
- Current odds
- Historical data
- Situational factors
- Risk adjustments

## Tips for Better Results

1. **Detailed Input**
   - Include team names
   - Specify bet types
   - Mention relevant conditions

2. **Multiple Analysis**
   - Compare different lines
   - Check alternate markets
   - Analyze various combinations

3. **Risk Management**
   - Review all warnings
   - Check correlation factors
   - Consider Kelly criterion sizing

4. **Market Timing**
   - Monitor line movements
   - Check for late updates
   - Consider timing recommendations

## Troubleshooting

### Common Issues

1. **Unclear Results**
   - Provide more specific input
   - Include all relevant details
   - Check for missing context

2. **High Risk Warnings**
   - Review all risk factors
   - Check for correlations
   - Consider reducing parlay size

3. **Low Confidence Scores**
   - Look for missing data
   - Check for recent updates
   - Consider waiting for more information

### Getting Help

If you encounter issues:
1. Check the documentation
2. Review example formats
3. Ensure all required data is provided
4. Contact support for persistent problems

## Limitations

The system:
- Requires current odds data
- Needs historical statistics
- May have delayed updates
- Cannot predict certainties

## Responsible Betting

Remember to:
- Set proper limits
- Follow bankroll management
- Consider all warnings
- Never chase losses
- Bet responsibly

## Updates and Maintenance

The system is regularly updated with:
- New sports coverage
- Enhanced analysis
- Improved correlations
- Better risk assessment

Check documentation for latest features and improvements. 