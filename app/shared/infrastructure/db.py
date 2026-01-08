from sqlmodel import SQLModel, create_engine
from sqlmodel import Session
from app.shared.core.config import settings
from app.modules.identity.domain.user import User
from app.modules.market.domain.kline import Kline
from app.modules.market.domain.ticker import Ticker
from app.modules.market.domain.order_book import OrderBook
from app.modules.market.domain.symbol_info import SymbolInfo

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

def create_db_and_tables():
    from app.modules.identity.domain.user import User
    from app.modules.subscription.domain.plan import SubscriptionPlan, PlanFeature 
    from app.modules.analysis.domain.entities import AnalysisResult
    SQLModel.metadata.create_all(engine)

# Alias for compatibility
def create_db_and_tables():
    """Initialize database and create all tables"""
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session