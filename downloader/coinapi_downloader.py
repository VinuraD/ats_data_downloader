"""
CoinAPI implementation of the base downloader
Handles all CoinAPI-specific logic and data formatting
"""

import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from .base_downloader import BaseDownloader


class CoinAPIDownloader(BaseDownloader):
    """CoinAPI implementation of cryptocurrency data downloader"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize CoinAPI downloader
        
        Args:
            api_key: CoinAPI key
            base_url: Base URL for CoinAPI (defaults to official API)
        """
        if base_url is None:
            base_url = 'https://rest.coinapi.io/v1'
        
        super().__init__(api_key, base_url)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for CoinAPI requests"""
        return {'X-CoinAPI-Key': self.api_key}
    
    def get_exchanges(self) -> Dict[str, Any]:
        """Get list of available exchanges from CoinAPI"""
        try:
            url = f'{self.base_url}/exchanges'
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                exchanges = response.json()
                # Filter for active exchanges with significant volume
                active_exchanges = [
                    ex for ex in exchanges 
                    if ex.get('volume_1day_usd', 0) > 1000000  # $1M+ daily volume
                ]
                return {
                    'success': True,
                    'exchanges': active_exchanges[:20]  # Top 20 exchanges
                }
            else:
                return {
                    'success': False,
                    'error': f'API Error: {response.status_code}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_symbols(self, search: str = "", exchange: str = "") -> Dict[str, Any]:
        """Get trading symbols from CoinAPI with search functionality"""
        try:
            # For now, return curated list of popular symbols
            # In production, you'd fetch from CoinAPI symbols endpoint
            popular_symbols = [
                {'symbol_id': 'BINANCE_SPOT_BTC_USDT', 'exchange_id': 'BINANCE', 'asset_id_base': 'BTC', 'asset_id_quote': 'USDT'},
                {'symbol_id': 'BINANCE_SPOT_ETH_USDT', 'exchange_id': 'BINANCE', 'asset_id_base': 'ETH', 'asset_id_quote': 'USDT'},
                {'symbol_id': 'BINANCE_SPOT_ADA_USDT', 'exchange_id': 'BINANCE', 'asset_id_base': 'ADA', 'asset_id_quote': 'USDT'},
                {'symbol_id': 'BINANCE_SPOT_DOT_USDT', 'exchange_id': 'BINANCE', 'asset_id_base': 'DOT', 'asset_id_quote': 'USDT'},
                {'symbol_id': 'BINANCE_SPOT_LINK_USDT', 'exchange_id': 'BINANCE', 'asset_id_base': 'LINK', 'asset_id_quote': 'USDT'},
                {'symbol_id': 'COINBASE_SPOT_BTC_USD', 'exchange_id': 'COINBASE', 'asset_id_base': 'BTC', 'asset_id_quote': 'USD'},
                {'symbol_id': 'COINBASE_SPOT_ETH_USD', 'exchange_id': 'COINBASE', 'asset_id_base': 'ETH', 'asset_id_quote': 'USD'},
                {'symbol_id': 'KRAKEN_SPOT_BTC_USD', 'exchange_id': 'KRAKEN', 'asset_id_base': 'BTC', 'asset_id_quote': 'USD'},
                {'symbol_id': 'KRAKEN_SPOT_ETH_USD', 'exchange_id': 'KRAKEN', 'asset_id_base': 'ETH', 'asset_id_quote': 'USD'},
            ]
            
            # Filter by search term
            if search:
                search_upper = search.upper()
                popular_symbols = [
                    s for s in popular_symbols 
                    if search_upper in s['symbol_id'] or search_upper in s['asset_id_base']
                ]
            
            # Filter by exchange
            if exchange:
                popular_symbols = [
                    s for s in popular_symbols 
                    if s['exchange_id'] == exchange.upper()
                ]
            
            return {
                'success': True,
                'symbols': popular_symbols
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_resolutions(self) -> Dict[str, Any]:
        """Get available candle resolutions from CoinAPI"""
        try:
            # Fetch periods from CoinAPI
            url = f'{self.base_url}/ohlcv/periods'
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                periods_data = response.json()
                
                # Process and categorize periods
                resolutions = []
                for period in periods_data:
                    category = 'Other'
                    if 'SEC' in period['period_id']:
                        category = 'Seconds'
                    elif 'MIN' in period['period_id']:
                        category = 'Minutes'
                    elif 'HRS' in period['period_id']:
                        category = 'Hours'
                    elif 'DAY' in period['period_id'] or 'WK' in period['period_id']:
                        category = 'Days'
                    elif 'MTH' in period['period_id'] or 'YR' in period['period_id']:
                        category = 'Months'
                    
                    resolutions.append({
                        'id': period['period_id'],
                        'name': period['display_name'],
                        'category': category,
                        'length_seconds': period.get('length_seconds', 0)
                    })
                
                # Sort by length_seconds for logical ordering
                resolutions.sort(key=lambda x: x['length_seconds'])
                
                return {
                    'success': True,
                    'resolutions': resolutions
                }
            else:
                # Fallback to hardcoded resolutions if API fails
                fallback_resolutions = [
                    {'id': '1MIN', 'name': '1 Minute', 'category': 'Minutes'},
                    {'id': '5MIN', 'name': '5 Minutes', 'category': 'Minutes'},
                    {'id': '15MIN', 'name': '15 Minutes', 'category': 'Minutes'},
                    {'id': '30MIN', 'name': '30 Minutes', 'category': 'Minutes'},
                    {'id': '1HRS', 'name': '1 Hour', 'category': 'Hours'},
                    {'id': '4HRS', 'name': '4 Hours', 'category': 'Hours'},
                    {'id': '1DAY', 'name': '1 Day', 'category': 'Days'},
                ]
                return {
                    'success': True,
                    'resolutions': fallback_resolutions
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_ohlcv(
        self,
        symbol: str,
        period_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Download OHLCV data from CoinAPI"""

        def _format_date(date_value: Optional[str], is_end: bool = False) -> Optional[str]:
            if not date_value:
                return None
            if len(date_value) == 10:  # YYYY-MM-DD
                suffix = "T23:59:59" if is_end else "T00:00:00"
                return f"{date_value}{suffix}"
            return date_value

        def _calculate_expected_candles(start_date: str, end_date: str, period_id: str) -> int:
            """Calculate expected number of candles based on date range and period"""
            from datetime import datetime, timedelta
            
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                # Period to timedelta mapping
                period_map = {
                    '1SEC': timedelta(seconds=1),
                    '2SEC': timedelta(seconds=2),
                    '3SEC': timedelta(seconds=3),
                    '5SEC': timedelta(seconds=5),
                    '10SEC': timedelta(seconds=10),
                    '15SEC': timedelta(seconds=15),
                    '20SEC': timedelta(seconds=20),
                    '30SEC': timedelta(seconds=30),
                    '1MIN': timedelta(minutes=1),
                    '2MIN': timedelta(minutes=2),
                    '3MIN': timedelta(minutes=3),
                    '5MIN': timedelta(minutes=5),
                    '10MIN': timedelta(minutes=10),
                    '15MIN': timedelta(minutes=15),
                    '20MIN': timedelta(minutes=20),
                    '30MIN': timedelta(minutes=30),
                    '1HRS': timedelta(hours=1),
                    '2HRS': timedelta(hours=2),
                    '3HRS': timedelta(hours=3),
                    '4HRS': timedelta(hours=4),
                    '6HRS': timedelta(hours=6),
                    '8HRS': timedelta(hours=8),
                    '12HRS': timedelta(hours=12),
                    '1DAY': timedelta(days=1),
                    '2DAY': timedelta(days=2),
                    '3DAY': timedelta(days=3),
                    '5DAY': timedelta(days=5),
                    '7DAY': timedelta(days=7),
                    '10DAY': timedelta(days=10),
                    '1MTH': timedelta(days=30),  # Approximate
                    '2MTH': timedelta(days=60),  # Approximate
                    '3MTH': timedelta(days=90),  # Approximate
                    '4MTH': timedelta(days=120), # Approximate
                    '6MTH': timedelta(days=180), # Approximate
                    '1YRS': timedelta(days=365), # Approximate
                }
                
                period_delta = period_map.get(period_id)
                if not period_delta:
                    return 10000  # Default large limit for unknown periods
                
                total_duration = end - start
                estimated_candles = int(total_duration / period_delta) + 50  # Add buffer
                
                # Cap at reasonable maximum (CoinAPI limit is 100,000)
                return min(estimated_candles, 50000)
            except Exception:
                return 10000  # Default fallback

        try:
            url = f"{self.base_url}/ohlcv/{symbol}/history"
            params: Dict[str, Any] = {"period_id": period_id}

            formatted_start = _format_date(start_date, is_end=False)
            formatted_end = _format_date(end_date, is_end=True)

            if formatted_start:
                params["time_start"] = formatted_start
            if formatted_end:
                params["time_end"] = formatted_end
            
            # Calculate appropriate limit based on date range
            if formatted_start and formatted_end:
                calculated_limit = _calculate_expected_candles(formatted_start, formatted_end, period_id)
                params["limit"] = calculated_limit
            elif limit:
                params["limit"] = limit

            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()

                if not data:
                    return {
                        'success': False,
                        'error': 'No data received from API',
                        'data': [],
                        'count': 0,
                    }

                return {
                    'success': True,
                    'data': data,
                    'count': len(data),
                }
            else:
                return {
                    'success': False,
                    'error': f'API Error: {response.status_code} - {response.text}',
                    'data': [],
                    'count': 0,
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'count': 0,
            }
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate CoinAPI symbol format"""
        # CoinAPI symbols typically follow EXCHANGE_TYPE_BASE_QUOTE format
        parts = symbol.split('_')
        return len(parts) >= 4 and parts[1] in ['SPOT', 'FUTURES', 'OPTION']
    
    def validate_resolution(self, period_id: str) -> bool:
        """Validate CoinAPI resolution format"""
        valid_periods = [
            '1SEC', '2SEC', '3SEC', '4SEC', '5SEC', '6SEC', '10SEC', '15SEC', '20SEC', '30SEC',
            '1MIN', '2MIN', '3MIN', '4MIN', '5MIN', '6MIN', '10MIN', '15MIN', '20MIN', '30MIN',
            '1HRS', '2HRS', '3HRS', '4HRS', '6HRS', '8HRS', '12HRS',
            '1DAY', '2DAY', '3DAY', '7DAY', '1MTH'
        ]
        return period_id in valid_periods
    
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert CoinAPI DataFrame format to standardized format"""
        # Convert timestamp
        df['time'] = pd.to_datetime(df['time_period_start'])
        
        # Create standardized DataFrame
        processed_df = pd.DataFrame({
            'time': df['time'],
            'open': df['price_open'],
            'high': df['price_high'],
            'low': df['price_low'],
            'close': df['price_close'],
            'volume': df['volume_traded'],
            'buy_volume': df['volume_traded'] * 0.55,  # Estimate (CoinAPI doesn't provide buy/sell split)
            'sell_volume': df['volume_traded'] * 0.45   # Estimate
        })
        
        return processed_df
    
    @property
    def platform_name(self) -> str:
        """Return platform name"""
        return "CoinAPI"
    
    @property
    def supported_features(self) -> List[str]:
        """Return supported features"""
        return [
            "OHLCV Data",
            "Multiple Exchanges", 
            "Historical Data",
            "Real-time Data",
            "Multiple Timeframes",
            "Symbol Search"
        ]

