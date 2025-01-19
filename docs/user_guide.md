# Sports Betting Analysis System User Guide

## Overview

The Sports Betting Analysis System helps analyze betting slips, focusing on player props and providing risk assessment for each bet.

## Features

### Bet Extraction
- Automatically extracts bets from betting slip images
- Handles OCR text correction
- Identifies player names, teams, and bet types
- Validates bet lines and odds

### Supported Bet Types
- Passing Yards
- Receiving Yards
- Other player props (expanding)

### Risk Analysis
The system analyzes each bet for:
- Line value assessment
- Odds evaluation
- Player performance context
- Team context impact

## Using the System

### Bet Slip Analysis

1. Submit a betting slip image
2. The system will:
   - Extract text using OCR
   - Identify valid bets
   - Skip unclear or incomplete bets
   - Analyze each valid bet

### Understanding Results

Each bet analysis includes:
1. **Player Information**
   - Name
   - Team
   - Bet type
   - Line
   - Odds

2. **Risk Assessment**
   - Overall risk level (High/Medium/Low)
   - Risk factors
   - Safety factors

3. **Context Analysis**
   - Player performance metrics
   - Team context
   - Historical averages

### Sample Output
```json
{
    "overall_risk": "Medium",
    "legs": [
        {
            "player": "Jalen Hurts",
            "bet_type": "Passing Yards",
            "line": 179.0,
            "odds": -186,
            "is_risky": false,
            "is_safe": true,
            "risk_factors": [],
            "safety_factors": ["Line below player average"]
        }
    ]
}
```

## Validation Rules

### Passing Yards
- Valid range: 150-400 yards
- Odds range: -500 to +500

### Receiving Yards
- Valid range: 20-150 yards
- Odds range: -500 to +500

## Best Practices

### Do's
1. Ensure betting slip image is clear
2. Wait for complete analysis
3. Review all risk factors
4. Check for missing bet information

### Don'ts
1. Submit unclear images
2. Ignore missing bet components
3. Skip risk assessment review

## Limitations

The system:
- Requires clear betting slip images
- May skip unclear player names
- Needs complete bet information
- Works best with player props

## Error Handling

Common scenarios:
1. **Unclear Player Names**
   - System will skip these bets
   - Example: "mauinew susnura" → skipped

2. **Missing Information**
   - Bets without lines or odds are skipped
   - Incomplete bet types are ignored

3. **Invalid Values**
   - Lines outside valid ranges are flagged
   - Extreme odds are validated

## Future Enhancements

Planned improvements:
- More bet types
- Enhanced player stats
- Additional sports coverage
- Improved OCR handling 