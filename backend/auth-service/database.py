from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

MYSQL_USER = os.getenv("DBUSER", "root")
MYSQL_PASSWORD = os.getenv("DBPWD", "password")
MYSQL_DB = os.getenv("DBNAME", "microtaskhub")
MYSQL_HOST = os.getenv("DBHOST", "localhost")
MYSQL_PORT = os.getenv("DBPORT", "3306")

ENCODED_PASSWORD = quote(MYSQL_PASSWORD, safe='')
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{ENCODED_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
