from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import users, tasks, dashboard, audit
from database import Base, engine, SessionLocal
from middleware import CorrelationIdMiddleware, get_correlation_id

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MicroTaskHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(CorrelationIdMiddleware)

app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)
app.include_router(audit.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": get_correlation_id(),
        },
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/ready")
def readiness_check():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not ready"})
