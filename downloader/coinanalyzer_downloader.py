"""
CoinAPI implementation of the base downloader
Handles all CoinAPI-specific logic and data formatting
"""

import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from .base_downloader import BaseDownloader
from datetime import datetime

class CoinAnalyzerDownloader(BaseDownloader):
    """CoinAPI implementation of cryptocurrency data downloader"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize CoinAPI downloader
        
        Args:
            api_key: CoinAPI key
            base_url: Base URL for CoinAPI (defaults to official API)
        """
        if base_url is None:
            base_url = 'https://api.coinalyze.net/v1'
        
        super().__init__(api_key, base_url)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for CoinAPI requests"""
        return {'api_key': self.api_key}
    
    def get_exchanges(self) -> Dict[str, Any]:
        """Get list of available exchanges from CoinAPI"""
        try:
            url = f'{self.base_url}/exchanges'
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                exchanges = response.json()
                # Filter for active exchanges with significant volume
                # active_exchanges = [
                #     ex for ex in exchanges 
                #     if ex.get('volume_1day_usd', 0) > 1000000  # $1M+ daily volume
                # ]
                # return {
                #     'success': True,
                #     'exchanges': active_exchanges[:20]  # Top 20 exchanges
                # }
                active_exchanges = ['H']  # For now, return only hyperliquid exchange
                return {
                    'success': True,
                    'exchanges': active_exchanges
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
            # popular_symbols = [
            #                 #     {'symbol_id': 'BINANCE_SPOT_ETH_USDT', 'exchange_id': 'BINANCE', 'asset_id_base': 'ETH', 'asset_id_quote': 'USDT'},
            #     {'symbol_id': 'BINANCE_SPOT_ADA_USDT', 'exchange_id': 'BINANCE', 'asset_id_base': 'ADA', 'asset_id_quote': 'USDT'},
            #     {'symbol_id': 'BINANCE_SPOT_DOT_USDT', 'exchange_id': 'BINANCE', 'asset_id_base': 'DOT', 'asset_id_quote': 'USDT'},
            #     {'symbol_id': 'BINANCE_SPOT_LINK_USDT', 'exchange_id': 'BINANCE', 'asset_id_base': 'LINK', 'asset_id_quote': 'USDT'},
            #     {'symbol_id': 'COINBASE_SPOT_BTC_USD', 'exchange_id': 'COINBASE', 'asset_id_base': 'BTC', 'asset_id_quote': 'USD'},
            #     {'symbol_id': 'COINBASE_SPOT_ETH_USD', 'exchange_id': 'COINBASE', 'asset_id_base': 'ETH', 'asset_id_quote': 'USD'},
            #     {'symbol_id': 'KRAKEN_SPOT_BTC_USD', 'exchange_id': 'KRAKEN', 'asset_id_base': 'BTC', 'asset_id_quote': 'USD'},
            #     {'symbol_id': 'KRAKEN_SPOT_ETH_USD', 'exchange_id': 'KRAKEN', 'asset_id_base': 'ETH', 'asset_id_quote': 'USD'},
            # ]

            #For now focus on hyperliquid exchange
            popular_symbols=[
                {'symbol_id': 'HYPE-USDC.H', 'exchange_id': 'H', 'asset_id_base': 'HYPE', 'asset_id_quote': 'USDC'},
                {'symbol_id': 'PURR-USDC.H', 'exchange_id': 'H', 'asset_id_base': 'PURR', 'asset_id_quote': 'USDC'},
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
            
            resolutions = [
                {'id': '1min', 'name': '1 Minute', 'category': 'Minutes'},
                {'id': '5min', 'name': '5 Minutes', 'category': 'Minutes'},
                {'id': '15min', 'name': '15 Minutes', 'category': 'Minutes'},
                {'id': '30min', 'name': '30 Minutes', 'category': 'Minutes'},
                {'id': '1hour', 'name': '1 Hour', 'category': 'Hours'},
                {'id': '2hour', 'name': '2 Hours', 'category': 'Hours'},
                {'id': '4hour', 'name': '4 Hours', 'category': 'Hours'},
                {'id': '6hour', 'name': '6 Hours', 'category': 'Hours'},
                {'id': '12hour', 'name': '12 Hours', 'category': 'Hours'},
                {'id': 'daily', 'name': '1 Day', 'category': 'Days'},
            ]
            return {
                'success': True,
                'resolutions': resolutions
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
        
        def _format_to_timestamp(date_value: Optional[str]) -> Optional[int]:
            if not date_value:
                return None
            if 'T' in date_value:
                date_value = datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%S")
                timestamp= int(date_value.timestamp())
                return timestamp

        try:
            url = f"{self.base_url}ohlcv-history/"
            params: Dict[str, Any] = {"interval": period_id}

            formatted_start = _format_to_timestamp(_format_date(start_date, is_end=False))
            formatted_end = _format_to_timestamp(_format_date(end_date, is_end=True))

            if formatted_start:
                params["from"] = formatted_start
            if formatted_end:
                params["to"] = formatted_end

            params["symbols"] = symbol
            # # Calculate appropriate limit based on date range
            # if formatted_start and formatted_end:
            #     calculated_limit = _calculate_expected_candles(formatted_start, formatted_end, period_id)
            #     params["limit"] = calculated_limit
            # elif limit:
            #     params["limit"] = limit

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
        
    #override base method
    def process_ohlcv_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        """
        Process raw OHLCV data into standardized DataFrame format
        
        Args:
            raw_data: Raw OHLCV data from API
            
        Returns:
            Processed DataFrame with columns: time, open, high, low, close, volume, buy_volume, sell_volume
        """
        if not raw_data:
            return pd.DataFrame()
        
        history = raw_data[0].get('history')
        df = pd.DataFrame(history)

        # Convert to standardized format
        processed_df = self._standardize_dataframe(df)
        
        # Sort by time (oldest first)
        processed_df = processed_df.sort_values('time').reset_index(drop=True)
        
        return processed_df
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate CoinAPI symbol format"""
        # CoinAPI symbols typically follow EXCHANGE_TYPE_BASE_QUOTE format
        parts = symbol.split('.')
        return len(parts) >= 2 and parts[1] in ['H']
    
    def validate_resolution(self, period_id: str) -> bool:
        """Validate CoinAPI resolution format"""
        valid_periods = [
            '1min', '5min', '15min', '30min',
            '1hour', '2hour', '4hour', '6hour', '12hour',
            'daily'
        ]
        return period_id in valid_periods
    
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert CoinAPI DataFrame format to standardized format"""
        # Convert timestamp to datetime
        df['t'] = df['t'].apply(lambda x: datetime.fromtimestamp(x))
        df['t'] = pd.to_datetime(df['t'])
        
        # Create standardized DataFrame
        processed_df = pd.DataFrame({
            'time': df['t'],
            'open': df['o'],
            'high': df['h'],
            'low': df['l'],
            'close': df['c'],
            'volume': df['v'],
            'buy_volume': df['bv'] * 0.55,  # Estimate (CoinAPI doesn't provide buy/sell split)
            'sell_volume': df['v'] - df['bv']
        })
        
        return processed_df
    
    @property
    def platform_name(self) -> str:
        """Return platform name"""
        return "CoinAnalyzer"
    
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

