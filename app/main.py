from fastapi import FastAPI
# Import router từ từng Feature slice
from app.modules.identity.features.register.router import router as register_router
from app.modules.identity.features.login.router import router as login_router
from app.modules.market.features.get_ai_analysis.router import router as ai_router
from app.modules.market.features.check_chart_access.router import router as chart_router

app = FastAPI(title="Modular Monolith Trading")


app.include_router(register_router, prefix="/api/v1", tags=["auth"])
app.include_router(login_router, prefix="/api/v1", tags=["auth"])

app.include_router(ai_router, prefix="/api/v1", tags=["market"])
app.include_router(chart_router, prefix="/api/v1", tags=["market"])

@app.get("/")
def root():
    return {"message": "System is running with Modular Monolith Architecture"}