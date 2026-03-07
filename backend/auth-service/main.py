from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, rbac, tasks, dashboard
from databse import Base, engine, SessionLocal
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

@app.on_event("startup")
def startup_db():
    db = SessionLocal()
    roles = ["User", "Manager", "Admin"]
    for role_name in roles:
        role = db.query(models.Role).filter(models.Role.name == role_name).first()
        if not role:
            role = models.Role(name=role_name, description=f"Default {role_name} role")
            db.add(role)
    db.commit()
    db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(rbac.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)

