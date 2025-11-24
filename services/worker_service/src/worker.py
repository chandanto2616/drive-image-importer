import os
import sys
import time
import logging
from urllib.parse import urlparse
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

from rq import Worker, Queue
from redis import Redis
import psycopg2
from shared.config import REDIS_URL, DATABASE_URL

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Logger setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# =====================================================
# Wait Functions
# =====================================================
def wait_for_redis(redis_url: str, timeout: int = 60) -> Redis:
    logger.info("⏳ Waiting for Redis...")
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            r = Redis.from_url(redis_url)
            if r.ping():
                logger.info("✅ Redis ready")
                return r
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError("Redis not ready")


def wait_for_postgres(database_url: str, timeout: int = 60):
    logger.info("⏳ Waiting for Postgres...")
    end_time = time.time() + timeout
    parsed = urlparse(database_url)
    while time.time() < end_time:
        try:
            conn = psycopg2.connect(
                dbname=parsed.path.lstrip('/'),
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port
            )
            conn.close()
            logger.info("✅ Postgres ready")
            return
        except Exception:
            time.sleep(2)
    raise TimeoutError("Postgres not ready")


# =====================================================
# Dummy HTTP Server
# =====================================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Worker running ✅")


def start_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    logger.info(f"🌐 Dummy HTTP server running on port {port}")
    server.serve_forever()


# =====================================================
# Main
# =====================================================
if __name__ == "__main__":
    # Start HTTP server in background
    Thread(target=start_dummy_server, daemon=True).start()

    # Prepare worker dependencies
    redis_conn = wait_for_redis(REDIS_URL)
    wait_for_postgres(DATABASE_URL)

    # Start worker (MAIN process, not thread)
    listen = ["default"]
    queues = [Queue(q, connection=redis_conn) for q in listen]
    worker = Worker(queues, connection=redis_conn)
    logger.info("🚀 Worker started, listening for jobs...")
    worker.work(with_scheduler=True)
