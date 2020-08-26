import json
import os
import re
from logging import getLogger

import psycopg2
import tweepy
from tweepy import OAuthHandler, Stream
from tweepy.streaming import StreamListener

logger = getLogger(__name__)

CK = os.environ.get("CONSUMER_KEY")
CS = os.environ.get("CONSUMER_SECRET")
AT = os.environ.get("ACCESS_TOKEN")
AS = os.environ.get("ACCESS_TOKEN_SECRET")


class QueueListener(StreamListener):
    def __init__(self, connection):
        super().__init__()

        self.auth = OAuthHandler(CK, CS)
        self.auth.set_access_token(AT, AS)
        self.api = tweepy.API(self.auth)
        self.lang = "ja"
        self.connection = connection
        self.sids_to_lookup = []
        self.statues_dict = {}
        self.max_tweet_num = 100
        self.max_conversation = int(os.environ.get("MAX_CONVERSATION", 10))
        self.min_conversation = int(os.environ.get("MIN_CONVERSATION", 2))
        self.min_statues = 10
        self.reply_user_id = {}
        self.reply_statues_id = {}

    @classmethod
    def stream(cls, connection):
        listener = cls(connection)
        return Stream(listener.auth, listener)

    def is_target_lang_tweet(self, status):
        return status.lang == self.lang

    @staticmethod
    def has_in_reply_to(status):
        return isinstance(status.in_reply_to_status_id, int)

    def on_status(self, status):
        if self.is_target_lang_tweet(status) and self.has_in_reply_to(status):
            self.reply_user_id[status.in_reply_to_user_id] = status.user.id
            self.reply_statues_id[status.in_reply_to_status_id] = [status.id]
            self.sids_to_lookup.append(status.in_reply_to_status_id)
            self.statues_dict[status.in_reply_to_status_id] = [status]

            if len(self.sids_to_lookup) >= self.max_tweet_num:
                logger.info("get ja tweet!")
                for i in range(self.max_conversation):
                    statues = self.api.statuses_lookup(self.sids_to_lookup)
                    self.sids_to_lookup = []
                    if len(statues) < self.min_statues and self.min_conversation > i:
                        self.reply_user_id = {}
                        self.reply_statues_id = {}
                        self.statues_dict = {}
                        self.sids_to_lookup = []
                        break

                    elif len(statues) < self.min_statues:
                        self.insert_conversation()
                        break

                    for status in statues:
                        if self.reply_user_id[status.user.id] == status.in_reply_to_user_id:
                            self.reply_user_id.pop(status.user.id)
                            self.reply_user_id[status.in_reply_to_user_id] = status.user.id
                            if status.in_reply_to_status_id is not None:
                                self.reply_statues_id[status.in_reply_to_status_id] = self.reply_statues_id.pop(status.id)
                                self.reply_statues_id[status.in_reply_to_status_id].append(status.id)
                                self.statues_dict[status.in_reply_to_status_id] = self.statues_dict.pop(status.id)
                                self.statues_dict[status.in_reply_to_status_id].append(status)
                                self.sids_to_lookup.append(status.in_reply_to_status_id)
                            else:
                                self.statues_dict[status.id].append(status)
                                self.reply_statues_id[status.id].append(status.id)
                else:
                    self.insert_conversation()

    def insert_conversation(self):
        [[self.insert_status(status) for status in statues] for statues in self.statues_dict.values() if len(statues) > self.min_conversation]

        with self.connection.cursor() as cursor:
            try:
                for value in self.reply_statues_id.values():
                    if len(value) > self.min_conversation:
                        cursor.execute(
                            "insert into conversation (ids) values (%s)",
                            (json.dumps({"ids": value}),)
                        )
            except psycopg2.errors.UniqueViolation as e:
                logger.error(e)
        self.connection.commit()
        self.reply_user_id = {}
        self.reply_statues_id = {}
        self.status_dict = {}
        self.sids_to_lookup = []
        logger.info("Done.")

    def insert_status(self, status):
        with self.connection.cursor() as cursor:
            text = self.sanitize_text(status.text)
            try:
                cursor.execute(
                    "insert into status "
                    "(id, text, in_reply_to_status_id, user_id, "
                    "created_at, is_quote_status) "
                    "values (%s, %s, %s, %s, %s, %s)",
                    [
                        status.id,
                        text,
                        status.in_reply_to_status_id,
                        status.user.id,
                        status.created_at.timestamp(),
                        int(status.is_quote_status)
                    ])
            except psycopg2.errors.UniqueViolation as e:
                # There can be same status already
                logger.error(e)
        self.connection.commit()

    @staticmethod
    def sanitize_text(text):
        return re.sub("\s+", ' ', text).strip()

    def on_error(self, status):
        logger.error('ON ERROR:', status)

    def on_limit(self, track):
        logger.error('ON LIMIT:', track)
