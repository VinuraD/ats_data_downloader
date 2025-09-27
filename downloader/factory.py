"""
Downloader factory for creating appropriate downloader instances
"""

from typing import Optional
from .base_downloader import BaseDownloader
from .coinapi_downloader import CoinAPIDownloader


class DownloaderFactory:
    """Factory class for creating downloader instances"""
    
    _downloaders = {
        'coinapi': CoinAPIDownloader,
        # Future downloaders will be added here
        # 'binance': BinanceDownloader,
        # 'kraken': KrakenDownloader,
    }
    
    @classmethod
    def create_downloader(cls, platform: str, api_key: str, base_url: Optional[str] = None) -> BaseDownloader:
        """
        Create a downloader instance for the specified platform
        
        Args:
            platform: Platform name (e.g., 'coinapi', 'binance')
            api_key: API key for the platform
            base_url: Optional base URL override
            
        Returns:
            Downloader instance
            
        Raises:
            ValueError: If platform is not supported
        """
        platform_lower = platform.lower()
        
        if platform_lower not in cls._downloaders:
            available = ', '.join(cls._downloaders.keys())
            raise ValueError(f"Unsupported platform '{platform}'. Available: {available}")
        
        downloader_class = cls._downloaders[platform_lower]
        return downloader_class(api_key, base_url)
    
    @classmethod
    def get_supported_platforms(cls) -> list:
        """Get list of supported platforms"""
        return list(cls._downloaders.keys())
    
    @classmethod
    def register_downloader(cls, platform: str, downloader_class: type):
        """
        Register a new downloader platform
        
        Args:
            platform: Platform name
            downloader_class: Downloader class that inherits from BaseDownloader
        """
        if not issubclass(downloader_class, BaseDownloader):
            raise ValueError("Downloader class must inherit from BaseDownloader")
        
        cls._downloaders[platform.lower()] = downloader_class

