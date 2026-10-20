"""
Headless Browser Crawler & Dependency Interceptor Package
"""

from .browser import BrowserCrawler
from .collector import DependencyGraphBuilder

__all__ = ["BrowserCrawler", "DependencyGraphBuilder"]
