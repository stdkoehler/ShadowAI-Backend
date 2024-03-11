""" FastAPI Server"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.textgen_webui import router as textgen_webui_router
from src.routers.session import router as session_router

# uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
# https://www.vidavolta.io/streaming-with-fastapi/


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(textgen_webui_router)
app.include_router(session_router)
