# twitter-dialogue-crawler
twitterの対話をクローリングする

# Get Started
1. `.env` ファイルに以下の環境変数を設定する

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

CONSUMER_KEY=XXXX
CONSUMER_SECRET=XXXX
ACCESS_TOKEN=XXXX
ACCESS_TOKEN_SECRET=XXXX

MAX_CONVERSATION=10 # 最大の対話数
MIN_CONVERSATION=2  # 最小の対話数 - 1
```

2. `docker-compose build && docker-compose up -d` で自動でクローリングを開始する

# REFERENCE
- https://github.com/higepon/twitter_conversation_crawler