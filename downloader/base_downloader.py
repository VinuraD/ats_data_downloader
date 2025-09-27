"""
Abstract base class for cryptocurrency data downloaders
Defines the interface that all downloader implementations must follow
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd


class BaseDownloader(ABC):
    """Abstract base class for cryptocurrency data downloaders"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize the downloader
        
        Args:
            api_key: API key for the data provider
            base_url: Base URL for the API (optional, uses default if not provided)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = self._build_headers()
    
    @abstractmethod
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for API requests"""
        pass
    
    @abstractmethod
    def get_exchanges(self) -> Dict[str, Any]:
        """
        Get list of available exchanges
        
        Returns:
            Dict with 'success' bool and 'exchanges' list
        """
        pass
    
    @abstractmethod
    def get_symbols(self, search: str = "", exchange: str = "") -> Dict[str, Any]:
        """
        Get trading symbols with optional search and exchange filter
        
        Args:
            search: Search term for symbol filtering
            exchange: Exchange filter
            
        Returns:
            Dict with 'success' bool and 'symbols' list
        """
        pass
    
    @abstractmethod
    def get_resolutions(self) -> Dict[str, Any]:
        """
        Get available candle resolutions/timeframes
        
        Returns:
            Dict with 'success' bool and 'resolutions' list
        """
        pass
    
    @abstractmethod
    def download_ohlcv(
        self,
        symbol: str,
        period_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Download OHLCV data for a symbol
        
        Args:
            symbol: Trading symbol identifier
            period_id: Time resolution (e.g., '1MIN', '1HRS', '1DAY')
            start_date: ISO formatted start date (YYYY-MM-DD or full timestamp)
            end_date: ISO formatted end date (YYYY-MM-DD or full timestamp)
            limit: Optional number of candles to fetch as fallback
        
        Returns:
            Dict with 'success' bool and keys:
              - 'data': list of OHLCV records
              - 'count': number of candles retrieved
        """
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is supported by this downloader
        
        Args:
            symbol: Trading symbol identifier
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_resolution(self, period_id: str) -> bool:
        """
        Validate if a resolution is supported by this downloader
        
        Args:
            period_id: Time resolution identifier
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
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
        
        df = pd.DataFrame(raw_data)
        
        # Convert to standardized format
        processed_df = self._standardize_dataframe(df)
        
        # Sort by time (oldest first)
        processed_df = processed_df.sort_values('time').reset_index(drop=True)
        
        return processed_df
    
    @abstractmethod
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert provider-specific DataFrame format to standardized format
        
        Args:
            df: Raw DataFrame from API
            
        Returns:
            Standardized DataFrame with required columns
        """
        pass
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the name of this downloader platform"""
        pass
    
    @property
    @abstractmethod
    def supported_features(self) -> List[str]:
        """Return list of supported features for this platform"""
        pass

