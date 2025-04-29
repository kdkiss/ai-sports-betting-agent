from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
import logging
import trafilatura
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import spacy

# Try to import AsyncDDGS, fall back to DDGS if not available
try:
    from duckduckgo_search import AsyncDDGS
    ASYNC_AVAILABLE = True
except ImportError:
    from duckduckgo_search import DDGS
    ASYNC_AVAILABLE = False

logger = logging.getLogger(__name__)

class SearchClient:
    """Client for gathering and analyzing web content related to sports betting."""
    
    def __init__(self):
        """Initialize the search client with NLP components and cache settings."""
        try:
            # Initialize NLP components
            nltk.download('vader_lexicon', quiet=True)
            self.nlp = spacy.load('en_core_web_sm')
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        except Exception as e:
            logger.error(f"Error initializing NLP components: {e}", exc_info=True)
            raise

        # Cache settings
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)
        
        # Search settings
        self.max_results = 5
        self.max_age_days = 2
        
        # Initialize DuckDuckGo search client
        if ASYNC_AVAILABLE:
            self.ddgs = AsyncDDGS()
        else:
            self.ddgs = DDGS()

    async def gather_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather and analyze relevant web content."""
        cache_key = self._generate_cache_key(context)
        
        # Check cache
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < self.cache_ttl:
                logger.debug(f"Returning cached insights for key: {cache_key}")
                return data
        
        # Gather data from multiple sources
        tasks = [
            self._search_news(context),
            self._search_expert_analysis(context),
            self._search_injury_updates(context),
            self._search_betting_trends(context)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in task {i}: {result}")
                    results[i] = []
        except Exception as e:
            logger.error(f"Error gathering insights: {e}", exc_info=True)
            results = [[], [], [], []]
        
        # Combine and analyze results
        insights = self._analyze_results(results, context)
        
        # Cache results
        self.cache[cache_key] = (datetime.now(), insights)
        logger.debug(f"Cached insights for key: {cache_key}")
        return insights
    
    async def _search_news(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for recent news articles."""
        query = self._build_news_query(context)
        articles = []
        
        try:
            if ASYNC_AVAILABLE:
                search_results = await self.ddgs.text(keywords=query, max_results=self.max_results)
            else:
                search_results = await asyncio.to_thread(self.ddgs.text, keywords=query, max_results=self.max_results)
            logger.debug(f"News search results for query '{query}': {search_results}")
            
            tasks = [self._extract_article(result['href']) for result in search_results]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Error extracting article: {result}")
                    continue
                if result:
                    articles.append(result)
        except Exception as e:
            logger.error(f"Error in news search for query '{query}': {e}", exc_info=True)
        
        return articles
    
    async def _search_expert_analysis(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for expert analysis and predictions."""
        query = self._build_expert_query(context)
        analyses = []
        
        try:
            if ASYNC_AVAILABLE:
                search_results = await self.ddgs.text(keywords=query, max_results=self.max_results)
            else:
                search_results = await asyncio.to_thread(self.ddgs.text, keywords=query, max_results=self.max_results)
            logger.debug(f"Expert analysis search results for query '{query}': {search_results}")
            
            tasks = [self._extract_article(result['href']) for result in search_results]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Error extracting article: {result}")
                    continue
                if result:
                    analyses.append(result)
        except Exception as e:
            logger.error(f"Error in expert analysis search for query '{query}': {e}", exc_info=True)
        
        return analyses
    
    async def _search_injury_updates(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for injury reports and updates."""
        if 'player' in context:
            query = f"{context['player']} injury update {context.get('sport', '')}"
        elif 'team1' in context and 'team2' in context:
            queries = [
                f"{context['team1']['name']} injury report {context.get('sport', '')}",
                f"{context['team2']['name']} injury report {context.get('sport', '')}"
            ]
        else:
            return []
            
        updates = []
        
        try:
            if isinstance(queries, list):
                for query in queries:
                    if ASYNC_AVAILABLE:
                        search_results = await self.ddgs.text(keywords=query, max_results=3)
                    else:
                        search_results = await asyncio.to_thread(self.ddgs.text, keywords=query, max_results=3)
                    logger.debug(f"Injury updates search results for query '{query}': {search_results}")
                    
                    tasks = [self._extract_article(result['href']) for result in search_results]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, Exception):
                            logger.warning(f"Error extracting article: {result}")
                            continue
                        if result:
                            updates.append(result)
            else:
                if ASYNC_AVAILABLE:
                    search_results = await self.ddgs.text(keywords=query, max_results=3)
                else:
                    search_results = await asyncio.to_thread(self.ddgs.text, keywords=query, max_results=3)
                logger.debug(f"Injury updates search results for query '{query}': {search_results}")
                
                tasks = [self._extract_article(result['href']) for result in search_results]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.warning(f"Error extracting article: {result}")
                        continue
                    if result:
                        updates.append(result)
        except Exception as e:
            logger.error(f"Error in injury updates search: {e}", exc_info=True)
        
        return updates
    
    async def _search_betting_trends(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for betting trends and line movements."""
        query = self._build_trends_query(context)
        trends = []
        
        try:
            if ASYNC_AVAILABLE:
                search_results = await self.ddgs.text(keywords=query, max_results=3)
            else:
                search_results = await asyncio.to_thread(self.ddgs.text, keywords=query, max_results=3)
            logger.debug(f"Betting trends search results for query '{query}': {search_results}")
            
            tasks = [self._extract_article(result['href']) for result in search_results]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Error extracting article: {result}")
                    continue
                if result:
                    trends.append(result)
        except Exception as e:
            logger.error(f"Error in betting trends search for query '{query}': {e}", exc_info=True)
        
        return trends
    
    async def _extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract and analyze article content."""
        try:
            downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
            if not downloaded:
                logger.debug(f"Failed to download article from {url}")
                return None
                
            content = await asyncio.to_thread(trafilatura.extract, downloaded)
            if not content:
                logger.debug(f"Failed to extract content from {url}")
                return None
            
            doc = await asyncio.to_thread(self.nlp, content)
            sentiment = await asyncio.to_thread(self.sentiment_analyzer.polarity_scores, content)
            
            article_data = {
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
            logger.debug(f"Extracted article data from {url}: {article_data}")
            return article_data
        except Exception as e:
            logger.warning(f"Error extracting article {url}: {e}")
            return None
    
    def _build_news_query(self, context: Dict[str, Any]) -> str:
        """Build search query for news."""
        components = []
        
        if 'player' in context:
            components.append(context['player'])
        if 'team1' in context:
            components.append(context['team1']['name'])
        if 'team2' in context:
            components.append(context['team2']['name'])
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
        if 'team1' in context:
            components.append(context['team1']['name'])
        if 'team2' in context:
            components.append(context['team2']['name'])
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
        if 'team1' in context:
            components.append(context['team1']['name'])
        if 'team2' in context:
            components.append(context['team2']['name'])
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
        
        all_sentiments = []
        for articles in results:
            for article in articles:
                if article and 'sentiment' in article:
                    all_sentiments.append(article['sentiment']['compound'])
        
        avg_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0
        
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
        
        logger.debug(f"Analyzed insights: {insights}")
        return insights
    
    def _extract_key_factors(self, results: List[List[Dict[str, Any]]]) -> List[str]:
        """Extract key factors from search results."""
        factors = []
        
        for articles in results:
            for article in articles:
                if not article or 'content' not in article:
                    continue
                    
                content = article['content'].lower()
                
                if 'injury' in content or 'injured' in content:
                    factors.append('Injury concerns mentioned')
                if 'weather' in content:
                    factors.append('Weather could be a factor')
                if 'streak' in content:
                    factors.append('Team/Player on notable streak')
                if 'line movement' in content or 'odds shift' in content:
                    factors.append('Significant line movement reported')
                    
        return list(set(factors))
    
    def _generate_cache_key(self, context: Dict[str, Any]) -> str:
        """Generate cache key from context."""
        components = []
        
        if 'player' in context:
            components.append(f"player_{context['player']}")
        if 'team1' in context:
            components.append(f"team_{context['team1']['name']}")
        if 'team2' in context:
            components.append(f"team_{context['team2']['name']}")
        if 'sport' in context:
            components.append(f"sport_{context['sport']}")
            
        return '_'.join(components)