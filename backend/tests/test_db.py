import os
import sys

# Add the backend dir to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, Base
import app.models  # This registers all models

def check_db():
    print(f"Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    table_names = engine.table_names() if hasattr(engine, 'table_names') else Base.metadata.tables.keys()
    
    print(f"Total tables created: {len(table_names)}")
    if len(table_names) != 68:
        print(f"ERROR: Expected 73 tables, found {len(table_names)}")
        return
        
    print("SUCCESS: 73 tables found.")
    
    # Import seed logic
    from app.main import seed_initial_data
    seed_initial_data()
    print("Seed data successfully loaded.")

if __name__ == "__main__":
    check_db()
