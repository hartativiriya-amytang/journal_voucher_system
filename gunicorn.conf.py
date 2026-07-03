import os

wsgi_app = 'journal_voucher_system.wsgi:application'

bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

workers = int(os.environ.get('GUNICORN_WORKERS', '4'))
threads = int(os.environ.get('GUNICORN_THREADS', '2'))
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gthread')

timeout = int(os.environ.get('GUNICORN_TIMEOUT', '120'))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', '5'))
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', '100'))

accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

reload = os.environ.get('GUNICORN_RELOAD', 'False').lower() in ('true', '1', 'yes')
