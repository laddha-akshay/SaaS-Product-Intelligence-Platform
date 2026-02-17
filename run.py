from fastapi import FastAPI
from app.api import router

app = FastAPI(title="SaaS Product Intelligence")
app.include_router(router)
