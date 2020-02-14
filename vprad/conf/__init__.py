import os
import environ


def get_env():
    ENV_FILE = os.environ.get('ENV_FILE',
                              os.path.join(os.getcwd(), '.env'))
    env = environ.Env()
    read_env = env.bool('READ_DOT_ENV_FILE', default=True)
    if read_env and os.path.exists(ENV_FILE):
        # OS environment variables take precedence over variables from .env
        env.read_env(ENV_FILE)
    return env


def default_internal_ips():
    """ Make sure INTERNAL_IPS has all our local IP addresses. """
    import socket
    internal_ips = ['127.0.0.1', ]
    hostname, _x, ips = socket.gethostbyname_ex(socket.gethostname())
    internal_ips += [ip[:-1] + '1' for ip in ips]
    return internal_ips


def default_wsgi():
    base = os.environ['DJANGO_SETTINGS_MODULE']
    path = base.split('.')[:-1]
    path.append('wsgi')
    path.append('application')
    return '.'.join(path)
