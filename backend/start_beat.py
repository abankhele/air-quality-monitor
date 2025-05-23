#!/usr/bin/env python
from celery_app import celery

if __name__ == '__main__':
    celery.start(['celery', 'beat', '--loglevel=info'])
