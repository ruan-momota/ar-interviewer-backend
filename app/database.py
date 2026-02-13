from sqlmodel import SQLModel, create_engine, Session

# Use SQLite file to restore interview.db
sqlite_file_name = "interview.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """Init database structure"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency Injection"""
    with Session(engine) as session:
        yield session