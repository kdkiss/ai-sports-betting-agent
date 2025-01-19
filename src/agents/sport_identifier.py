from typing import List, Set

class SportIdentifier:
    """Identifies sports from betting text using keyword analysis."""

    # Sport-specific keywords and patterns
    SPORT_INDICATORS = {
        'NFL': {
            'teams': {'chiefs', 'ravens', 'eagles', '49ers', 'bills'},
            'positions': {'qb', 'quarterback', 'rb', 'wr', 'te'},
            'stats': {'passing yards', 'rushing yards', 'receiving yards', 'touchdowns', 'interceptions', 'sacks'},
            'terms': {'football', 'nfl', 'touchdown', 'field goal'}
        },
        'NBA': {
            'teams': {'lakers', 'celtics', 'warriors', 'bulls', 'nets'},
            'positions': {'pg', 'sg', 'sf', 'pf', 'center'},
            'stats': {'points', 'rebounds', 'assists', 'steals', 'blocks', '3-pointers', 'threes'},
            'terms': {'basketball', 'nba', 'quarter', 'paint'}
        },
        'MLB': {
            'teams': {'yankees', 'dodgers', 'red sox', 'cubs', 'mets'},
            'positions': {'pitcher', 'catcher', 'infielder', 'outfielder'},
            'stats': {'strikeouts', 'hits', 'runs', 'home runs', 'rbis', 'era'},
            'terms': {'baseball', 'mlb', 'innings', 'batting'}
        },
        'NHL': {
            'teams': {'bruins', 'rangers', 'maple leafs', 'canadiens'},
            'positions': {'goalie', 'defenseman', 'center', 'wing'},
            'stats': {'goals', 'assists', 'saves', 'shots on goal'},
            'terms': {'hockey', 'nhl', 'period', 'power play'}
        },
        'UFC': {
            'terms': {'ufc', 'mma', 'fight', 'fighter', 'octagon'},
            'stats': {'significant strikes', 'takedowns', 'submissions'},
            'outcomes': {'ko', 'tko', 'submission', 'decision'},
            'positions': {'heavyweight', 'lightweight', 'welterweight'}
        },
        'Soccer': {
            'teams': {'manchester', 'liverpool', 'arsenal', 'chelsea'},
            'positions': {'striker', 'midfielder', 'defender', 'goalkeeper'},
            'stats': {'goals', 'assists', 'clean sheet', 'shots on target'},
            'terms': {'soccer', 'football', 'premier league', 'la liga', 'bundesliga'}
        }
    }

    def identify_sports(self, text: str) -> List[str]:
        """
        Identify all sports referenced in the text.
        
        Args:
            text: The betting text to analyze
            
        Returns:
            List of identified sports
        """
        text = text.lower()
        words = set(text.split())
        found_sports = set()

        # Check each sport's indicators
        for sport, indicators in self.SPORT_INDICATORS.items():
            if self._check_sport_indicators(text, words, indicators):
                found_sports.add(sport)

        return list(found_sports)

    def _check_sport_indicators(self, text: str, words: Set[str], indicators: dict) -> bool:
        """Check if text matches any indicators for a sport."""
        for category in indicators.values():
            # Check for exact matches in word set
            if any(term in words for term in category):
                return True
            
            # Check for phrase matches in full text
            if any(term in text for term in category if ' ' in term):
                return True
        
        return False

    def get_sport_specific_context(self, text: str, sport: str) -> dict:
        """
        Extract sport-specific context from text.
        
        Args:
            text: The betting text to analyze
            sport: The identified sport
            
        Returns:
            Dictionary with sport-specific context
        """
        context = {
            'sport': sport,
            'keywords': set()
        }

        # Add found keywords to context
        text_lower = text.lower()
        for category, terms in self.SPORT_INDICATORS[sport].items():
            found = {term for term in terms if term in text_lower}
            if found:
                context['keywords'].update(found)
                context[category] = found

        return context 