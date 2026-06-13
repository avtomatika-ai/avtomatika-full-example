from os import environ
from os.path import abspath, dirname, join
from avtomatika.config import Config

PROJECT_ROOT = dirname(abspath(__file__))

config = Config()

config.API_PORT = 8080
config.LOG_LEVEL = "INFO"

config.REDIS_HOST = environ.get("REDIS_HOST", "localhost")
config.REDIS_PORT = 6379

config.HISTORY_DATABASE_URI = environ.get(
    "HISTORY_DATABASE_URI", "postgresql://user:password@localhost:5432/avtomatika"
)

config.S3_ENDPOINT_URL = environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
config.S3_ACCESS_KEY = environ.get("S3_ACCESS_KEY", "minioadmin")
config.S3_SECRET_KEY = environ.get("S3_SECRET_KEY", "minioadmin")
config.S3_DEFAULT_BUCKET = "avtomatika-payloads"

config.BLUEPRINTS_DIR = join(PROJECT_ROOT, "blueprints")

config.CLIENTS_CONFIG_PATH = environ.get(
    "CLIENTS_CONFIG_PATH", join(PROJECT_ROOT, "example_clients.toml")
)
config.WORKERS_CONFIG_PATH = environ.get(
    "WORKERS_CONFIG_PATH", join(PROJECT_ROOT, "example_workers.toml")
)

config.GLOBAL_WORKER_TOKEN = "super-secret-worker-token"

config.REPUTATION_PENALTY_CONTRACT_VIOLATION = 0.2
config.REPUTATION_MIN_THRESHOLD = 0.3

config.SCHEDULES_CONFIG_PATH = environ.get(
    "SCHEDULES_CONFIG_PATH", join(PROJECT_ROOT, "schedules.toml")
)

config.EXECUTOR_MAX_CONCURRENT_JOBS = 100
config.RATE_LIMITING_ENABLED = False
config.WORK_STEALING_ENABLED = False
