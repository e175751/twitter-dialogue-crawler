import http.client
import logging
import os
import socket
import sys
import time
from logging import getLogger

import psycopg2
import urllib3

from twitterListener import QueueListener

logging.basicConfig(level=os.environ.get("LOG_LEVEL", logging.DEBUG))
logger = getLogger(__name__)

USER = os.environ.get("POSTGRES_USER", "postgres")
PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
DB = os.environ.get("POSTGRES_DB", USER)
DATABASE_URL = f'postgresql://{USER}:{PASSWORD}@db:5432/{DB}'


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def main():
    with get_connection() as connection:
        stream = QueueListener.stream(connection)

        logger.info("Listening...\n")
        delay = 0.25
        while True:
            try:
                stream.sample()
            except KeyboardInterrupt:
                sys.exit()
            except urllib3.exceptions.ProtocolError as e:
                logger.error("Incomplete read", e)
            except urllib3.exceptions.ReadTimeoutError as e:
                logger.error("Read Timeout", e)
            except (socket.error, http.client.HTTPException):
                logger.error("HTTP error waiting for a few seconds")
                time.sleep(delay)
                delay += 0.25

if __name__ == '__main__':
    main()
