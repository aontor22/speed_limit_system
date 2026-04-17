from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 1. Database Configuration
# Format: postgresql://[user]:[password]@[host]:[port]/[database_name]
DATABASE_URL = "postgresql://postgres:11Udoy##@localhost:5432/traffic_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Violation Table Model
class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    detected_speed = Column(Integer)
    speed_limit = Column(Integer)
    status = Column(String) # e.g., "Over-speeding"

# 3. Auto-Create Table
def init_db():
    Base.metadata.create_all(bind=engine)

# 4. Helper to save violation
def save_violation(speed, limit):
    db = SessionLocal()
    try:
        new_violation = Violation(
            detected_speed=speed,
            speed_limit=limit,
            status="Over-speeding"
        )
        db.add(new_violation)
        db.commit()
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        db.close()