import os

from dotenv import load_dotenv

load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

MAX_FILES = int(
    os.getenv("MAX_FILES", "2000")
)

MAX_CONTRIBUTORS = int(
    os.getenv("MAX_CONTRIBUTORS", "100")
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
)