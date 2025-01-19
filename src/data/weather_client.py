from typing import Dict, Any, Optional
import aiohttp
from datetime import datetime, timedelta
import os

class WeatherClient:
    """Client for fetching weather data for outdoor sports."""
    
    def __init__(self):
        self.api_key = os.getenv('WEATHER_API_KEY')
        self.base_url = "https://api.weatherapi.com/v1"
        self.cache = {}
        
        # Stadium locations for outdoor sports
        self.stadium_locations = {
            'NFL': {
                'chiefs': 'Kansas City,MO',
                'bills': 'Orchard Park,NY',
                'packers': 'Green Bay,WI',
                # Add more NFL stadiums
            },
            'MLB': {
                'yankees': 'Bronx,NY',
                'red_sox': 'Boston,MA',
                'cubs': 'Chicago,IL',
                # Add more MLB stadiums
            }
        }
    
    async def get_forecast(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather forecast for a game."""
        location = self._get_location(context)
        if not location:
            return {"error": "Could not determine game location"}
            
        cache_key = f"{location}_{context.get('game_time', 'today')}"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=1):
                return data
        
        # Fetch weather data
        forecast = await self._fetch_forecast(location, context)
        
        # Cache results
        self.cache[cache_key] = (datetime.now(), forecast)
        return forecast
    
    def _get_location(self, context: Dict[str, Any]) -> Optional[str]:
        """Determine location based on context."""
        sport = context.get('sport', '')
        if sport not in self.stadium_locations:
            return None
            
        team = context.get('team', '').lower()
        return self.stadium_locations[sport].get(team)
    
    async def _fetch_forecast(self, location: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch weather forecast from API."""
        game_time = context.get('game_time', 'today')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/forecast.json",
                params={
                    'key': self.api_key,
                    'q': location,
                    'days': 3,  # Get 3-day forecast to cover upcoming games
                    'aqi': 'no'
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_forecast(data, game_time)
                else:
                    return {"error": f"Failed to fetch weather data: {response.status}"}
    
    def _process_forecast(self, data: Dict[str, Any], game_time: str) -> Dict[str, Any]:
        """Process raw weather data into relevant format."""
        processed = {
            'current': {
                'temp_f': data['current']['temp_f'],
                'condition': data['current']['condition']['text'],
                'wind_mph': data['current']['wind_mph'],
                'wind_dir': data['current']['wind_dir'],
                'precip_in': data['current']['precip_in'],
                'humidity': data['current']['humidity']
            },
            'forecast': [],
            'game_impact': self._assess_weather_impact(data['current'])
        }
        
        # Add hourly forecast if available
        if 'forecast' in data and 'forecastday' in data['forecast']:
            for day in data['forecast']['forecastday']:
                processed['forecast'].append({
                    'date': day['date'],
                    'max_temp_f': day['day']['maxtemp_f'],
                    'min_temp_f': day['day']['mintemp_f'],
                    'condition': day['day']['condition']['text'],
                    'max_wind_mph': day['day']['maxwind_mph'],
                    'total_precip_in': day['day']['totalprecip_in']
                })
        
        return processed
    
    def _assess_weather_impact(self, weather: Dict[str, Any]) -> Dict[str, Any]:
        """Assess potential impact of weather on the game."""
        impact = {
            'overall_rating': 'neutral',  # negative, neutral, positive
            'factors': [],
            'recommendations': []
        }
        
        # Temperature impact
        if weather['temp_f'] < 32:
            impact['factors'].append('freezing_temperatures')
            impact['recommendations'].append('Cold weather may affect ball handling and kicking')
        elif weather['temp_f'] > 90:
            impact['factors'].append('extreme_heat')
            impact['recommendations'].append('Heat may affect player stamina')
            
        # Wind impact
        if weather['wind_mph'] > 15:
            impact['factors'].append('high_winds')
            impact['recommendations'].append('Strong winds may affect passing and kicking game')
            
        # Precipitation impact
        if weather['precip_in'] > 0:
            impact['factors'].append('precipitation')
            impact['recommendations'].append('Wet conditions may affect ball handling')
            
        # Set overall rating
        if len(impact['factors']) >= 2:
            impact['overall_rating'] = 'negative'
        elif len(impact['factors']) == 0:
            impact['overall_rating'] = 'positive'
            
        return impact 