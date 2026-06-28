from fastapi import FastAPI
from .routes import applications, CompanyTimeline
from .db import init_db, engine, Base
from fastapi.middleware.cors import CORSMiddleware
from .services.imap_service import fetch_sent_applications
import asyncio
from .services.imap_service import fetch_sent_applications, process_ai_queue

app = FastAPI(title="Internship Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # the Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # --- Create database tables automatically ---
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # --- Start periodic email fetch ---
    async def periodic_fetch():
        while True:
            try:
                await fetch_sent_applications()  # Phase 1: Fast Ingest
                await process_ai_queue()         # Phase 2: Slow AI Processing
            except Exception as e:
                print(f"Error during loop: {e}", flush=True)
            await asyncio.sleep(60 * 5)

    asyncio.create_task(periodic_fetch())


# --- Routers ---
app.include_router(applications.router, prefix="/applications")
app.include_router(CompanyTimeline.router, prefix="/company")


@app.get("/")
def root():
    return {"message": "Internship Tracker API running"}




