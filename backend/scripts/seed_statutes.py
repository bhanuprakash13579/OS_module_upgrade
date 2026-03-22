import os
import sys

# Add backend directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import Base, SessionLocal, engine
from app.models.statutes import LegalStatute
from app.scripts.statutes_data import DEFAULT_STATUTES


def seed_db():
    db: Session = SessionLocal()
    try:
        count = 0
        for statute_data in DEFAULT_STATUTES:
            existing = db.query(LegalStatute).filter(
                LegalStatute.keyword == statute_data["keyword"]
            ).first()
            if not existing:
                statute = LegalStatute(**statute_data)
                db.add(statute)
                count += 1
        db.commit()
        print(f"Successfully seeded {count} new legal statutes.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_db()
