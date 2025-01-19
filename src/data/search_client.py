from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
import os
from bs4 import BeautifulSoup
from googlesearch import search
from newspaper import Article
import feedparser
import trafilatura
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import spacy

class SearchClient:
    """Client for gathering and analyzing web content related to sports betting."""
    
    def __init__(self):
        # Initialize NLP components
        nltk.download('vader_lexicon', quiet=True)
        self.nlp = spacy.load('en_core_web_sm')
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Cache settings
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)
        
        # Search settings
        self.max_results = 10
        self.max_age_days = 2
        
    async def gather_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather and analyze relevant web content."""
        cache_key = self._generate_cache_key(context)
        
        # Check cache
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < self.cache_ttl:
                return data
        
        # Gather data from multiple sources
        tasks = [
            self._search_news(context),
            self._search_expert_analysis(context),
            self._search_injury_updates(context),
            self._search_betting_trends(context)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Combine and analyze results
        insights = self._analyze_results(results, context)
        
        # Cache results
        self.cache[cache_key] = (datetime.now(), insights)
        return insights
    
    async def _search_news(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for recent news articles."""
        query = self._build_news_query(context)
        articles = []
        
        try:
            # Search for news articles
            search_results = search(query, num=self.max_results, stop=self.max_results)
            
            for url in search_results:
                article = await self._extract_article(url)
                if article:
                    articles.append(article)
        except Exception as e:
            print(f"Error in news search: {e}")
        
        return articles
    
    async def _search_expert_analysis(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for expert analysis and predictions."""
        query = self._build_expert_query(context)
        analyses = []
        
        try:
            # Search sports analysis sites
            search_results = search(
                query,
                num=self.max_results,
                stop=self.max_results
            )
            
            for url in search_results:
                analysis = await self._extract_article(url)
                if analysis:
                    analyses.append(analysis)
        except Exception as e:
            print(f"Error in expert analysis search: {e}")
        
        return analyses
    
    async def _search_injury_updates(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for injury reports and updates."""
        if 'player' in context:
            query = f"{context['player']} injury update {context.get('sport', '')}"
        elif 'team' in context:
            query = f"{context['team']} injury report {context.get('sport', '')}"
        else:
            return []
            
        updates = []
        
        try:
            search_results = search(query, num=5, stop=5)
            
            for url in search_results:
                update = await self._extract_article(url)
                if update:
                    updates.append(update)
        except Exception as e:
            print(f"Error in injury updates search: {e}")
        
        return updates
    
    async def _search_betting_trends(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for betting trends and line movements."""
        query = self._build_trends_query(context)
        trends = []
        
        try:
            search_results = search(query, num=5, stop=5)
            
            for url in search_results:
                trend = await self._extract_article(url)
                if trend:
                    trends.append(trend)
        except Exception as e:
            print(f"Error in trends search: {e}")
        
        return trends
    
    async def _extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract and analyze article content."""
        try:
            # Download and parse article
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
                
            content = trafilatura.extract(downloaded)
            if not content:
                return None
            
            # Analyze content
            doc = self.nlp(content)
            sentiment = self.sentiment_analyzer.polarity_scores(content)
            
            return {
                'url': url,
                'content': content,
                'summary': ' '.join([sent.text for sent in doc.sents][:3]),
                'sentiment': sentiment,
                'entities': [
                    {'text': ent.text, 'label': ent.label_}
                    for ent in doc.ents
                    if ent.label_ in ['PERSON', 'ORG', 'GPE', 'DATE']
                ],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error extracting article {url}: {e}")
            return None
    
    def _build_news_query(self, context: Dict[str, Any]) -> str:
        """Build search query for news."""
        components = []
        
        if 'player' in context:
            components.append(context['player'])
        if 'team' in context:
            components.append(context['team'])
        if 'sport' in context:
            components.append(context['sport'])
            
        components.append('news')
        components.append('latest')
        
        return ' '.join(components)
    
    def _build_expert_query(self, context: Dict[str, Any]) -> str:
        """Build search query for expert analysis."""
        components = []
        
        if 'player' in context:
            components.append(context['player'])
        if 'team' in context:
            components.append(context['team'])
        if 'sport' in context:
            components.append(context['sport'])
            
        components.append('prediction')
        components.append('analysis')
        components.append('expert')
        
        return ' '.join(components)
    
    def _build_trends_query(self, context: Dict[str, Any]) -> str:
        """Build search query for betting trends."""
        components = []
        
        if 'player' in context:
            components.append(context['player'])
        if 'team' in context:
            components.append(context['team'])
        if 'sport' in context:
            components.append(context['sport'])
            
        components.append('betting')
        components.append('trends')
        components.append('line movement')
        
        return ' '.join(components)
    
    def _analyze_results(
        self,
        results: List[List[Dict[str, Any]]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze and combine search results."""
        news, expert_analysis, injury_updates, trends = results
        
        # Aggregate sentiments
        all_sentiments = []
        for articles in results:
            for article in articles:
                if article and 'sentiment' in article:
                    all_sentiments.append(article['sentiment']['compound'])
        
        avg_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0
        
        # Extract key insights
        insights = {
            'overall_sentiment': {
                'score': avg_sentiment,
                'interpretation': (
                    'Positive' if avg_sentiment > 0.2
                    else 'Negative' if avg_sentiment < -0.2
                    else 'Neutral'
                )
            },
            'news_summary': [
                article['summary'] for article in news
                if article and 'summary' in article
            ][:3],
            'expert_opinions': [
                article['summary'] for article in expert_analysis
                if article and 'summary' in article
            ][:3],
            'injury_notes': [
                article['summary'] for article in injury_updates
                if article and 'summary' in article
            ][:2],
            'betting_trends': [
                article['summary'] for article in trends
                if article and 'summary' in article
            ][:2],
            'key_factors': self._extract_key_factors(results),
            'timestamp': datetime.now().isoformat()
        }
        
        return insights
    
    def _extract_key_factors(self, results: List[List[Dict[str, Any]]]) -> List[str]:
        """Extract key factors from search results."""
        factors = []
        
        # Analyze all content for key insights
        for articles in results:
            for article in articles:
                if not article or 'content' not in article:
                    continue
                    
                # Look for key phrases
                content = article['content'].lower()
                
                if 'injury' in content or 'injured' in content:
                    factors.append('Injury concerns mentioned')
                if 'weather' in content:
                    factors.append('Weather could be a factor')
                if 'streak' in content:
                    factors.append('Team/Player on notable streak')
                if 'line movement' in content or 'odds shift' in content:
                    factors.append('Significant line movement reported')
                    
        # Remove duplicates and return
        return list(set(factors))
    
    def _generate_cache_key(self, context: Dict[str, Any]) -> str:
        """Generate cache key from context."""
        components = []
        
        if 'player' in context:
            components.append(f"player_{context['player']}")
        if 'team' in context:
            components.append(f"team_{context['team']}")
        if 'sport' in context:
            components.append(f"sport_{context['sport']}")
            
        return '_'.join(components) 