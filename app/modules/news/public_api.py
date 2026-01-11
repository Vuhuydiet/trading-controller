"""Public API for News Module"""

from app.modules.news.features.get_insights.router import router as get_insights_router
from app.modules.news.features.get_latest_news.router import router as get_news_router

__all__ = ["get_news_router", "get_insights_router"]
