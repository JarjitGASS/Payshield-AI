from fastapi import FastAPI, Query
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok"}