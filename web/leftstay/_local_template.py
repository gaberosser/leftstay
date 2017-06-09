TRANSACTION_CHUNK_SIZE = 50000

# 'From' field in header if supplied (email address)
REQUEST_FROM = None

DEFAULT_USER_AGENT = 'leftstay-agent-55'
LOGFILE_BACKUP_COUNT = 30  # ~ 1 mo  of log files

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': 'local_outputs/leftstay.log',
            'backupCount': LOGFILE_BACKUP_COUNT,
            'when': 'midnight',
            'formatter': 'simple'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'rightmove': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }
    },
}