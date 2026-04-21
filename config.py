from os import environ
from os.path import abspath, dirname, join
from avtomatika.config import Config

# Build absolute paths to config files relative to the project root
# Assuming this file is in the root or imported such that dirname(abspath(__file__)) is the root
PROJECT_ROOT = dirname(abspath(__file__))

config = Config()

# Basic Orchestrator Settings
config.API_PORT = 8080
config.LOG_LEVEL = "INFO"

# Storage Configuration
config.REDIS_HOST = environ.get("REDIS_HOST", "localhost")
config.REDIS_PORT = 6379

# SQLAlchemy History Storage (PostgreSQL)
config.HISTORY_DATABASE_URI = environ.get(
    "HISTORY_DATABASE_URI", "postgresql://user:password@localhost:5432/avtomatika"
)

# S3 Artifact Storage (MinIO)
config.S3_ENDPOINT_URL = environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
config.S3_ACCESS_KEY = environ.get("S3_ACCESS_KEY", "minioadmin")
config.S3_SECRET_KEY = environ.get("S3_SECRET_KEY", "minioadmin")
config.S3_DEFAULT_BUCKET = "avtomatika-payloads"

# Blueprint Loading
config.BLUEPRINTS_DIR = join(PROJECT_ROOT, "blueprints")

# Auth Configuration
# We use example TOML files provided in the repository
config.CLIENTS_CONFIG_PATH = environ.get(
    "CLIENTS_CONFIG_PATH", join(PROJECT_ROOT, "example_clients.toml")
)
config.WORKERS_CONFIG_PATH = environ.get(
    "WORKERS_CONFIG_PATH", join(PROJECT_ROOT, "example_workers.toml")
)

# Disable strict Zero Trust signatures for the demo if requested
config.GLOBAL_WORKER_TOKEN = None

# Reliability and Reputation
config.REPUTATION_ENABLED = True
config.REPUTATION_OFFLINE_THRESHOLD = 0.3
config.REPUTATION_PENALTY_CONTRACT_VIOLATION = 0.2

# Scheduling
config.SCHEDULES_CONFIG_PATH = environ.get(
    "SCHEDULES_CONFIG_PATH", join(PROJECT_ROOT, "schedules.toml")
)

# Capacity and Concurrency
config.EXECUTOR_MAX_CONCURRENT_JOBS = 100
config.ENABLE_METRICS = True
config.RATE_LIMITING_ENABLED = False
config.WORK_STEALING_ENABLED = False
