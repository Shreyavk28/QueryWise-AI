
import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

load_dotenv()

database_url = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.environ["DB_NAME"],
    query={"charset": "utf8mb4"},
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)


def check_database():
    with engine.connect() as connection:
        return connection.execute(text("SELECT 1")).scalar_one()


if __name__ == "__main__":
    print("Checking MySQL connection...")

    try:
        result = check_database()
        print(f"MySQL connected successfully! Test result: {result}")
    except Exception as exc:
        print(f"MySQL connection failed: {exc}")
