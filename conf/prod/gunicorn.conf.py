import multiprocessing

backlog = 2048
daemon = False
debug = False
spew = False
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 450
max_requests_jitter = 50
bind = "unix:/home/projects/passkeys_example/passkeys_example/tmp/gunicorn.sock"
pidfile = "/home/projects/passkeys_example/passkeys_example/tmp/gunicorn.pid"
logfile = "/home/projects/passkeys_example/passkeys_example/logs/gunicorn.log"
loglevel = "error"
user = "passkeys_example"
proc_name = "passkeys_example"
timeout = 60
