import urllib.parse
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# -------------------------------
# 1. Database Configuration (FIXED PASSWORD ENCODING)
# -------------------------------

# Encode special characters in password (## → %23%23)
password = urllib.parse.quote_plus("11Udoy##")

DATABASE_URL = f"postgresql://postgres:{password}@localhost:5432/traffic_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------------
# 2. Violation Table Model
# -------------------------------

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    detected_speed = Column(Integer)
    speed_limit = Column(Integer)
    status = Column(String)  # e.g., "Over-speeding"

# -------------------------------
# 3. Initialize Database
# -------------------------------

def init_db():
    Base.metadata.create_all(bind=engine)

# -------------------------------
# 4. Save Violation (FIXED + DEBUG)
# -------------------------------

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

        # Debug print (VERY useful)
        print(f"Saved violation: speed={speed}, limit={limit}")

    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        db.close()

# -------------------------------
# 5. Get Recent Violations (FIXED)
# -------------------------------

def get_recent_violations(limit=10):
    db = SessionLocal()
    try:
        records = db.query(Violation).order_by(Violation.id.desc()).limit(limit).all()

        return [
            {
                "id": v.id,
                "timestamp": v.timestamp.strftime("%H:%M:%S"),
                "detected_speed": v.detected_speed,
                "speed_limit": v.speed_limit,
                "status": v.status
            }
            for v in records
        ]

    except Exception as e:
        print(f"DB Fetch Error: {e}")
        return []

    finally:
        db.close()