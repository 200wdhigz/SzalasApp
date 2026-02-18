# Gunicorn configuration file for production deployment
# Usage: gunicorn -c gunicorn.conf.py app:app

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
threads = int(os.getenv('GUNICORN_THREADS', 2))
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "szalas-app"

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Szałas App with Gunicorn")
    server.log.info(f"Workers: {workers}, Threads: {threads}")
    server.log.info(f"Binding to: {bind}")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Szałas App")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Szałas App is ready to serve requests")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")

# SSL/HTTPS (if you need direct HTTPS - usually not needed with reverse proxy)
# keyfile = None
# certfile = None
# ssl_version = 2
# cert_reqs = 0
# ca_certs = None
# suppress_ragged_eofs = True
# do_handshake_on_connect = False
# ciphers = None

# Forwarded headers (important for reverse proxy)
forwarded_allow_ips = os.getenv('FORWARDED_ALLOW_IPS', '*')

# Preload app for faster worker startup
preload_app = False

# Restart workers gracefully on code change (dev only)
reload = os.getenv('GUNICORN_RELOAD', 'False').lower() in ('true', '1', 'yes')
reload_engine = 'auto'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

