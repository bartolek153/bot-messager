# Bot Messenger 

A python script, scheduled to run periodically, which analyzes the latest contents of HTML pages, processes them and sends the obtained data to a Telegram channel.

## Install and run with Docker

```bash
curl -sSL https://raw.githubusercontent.com/bartolek153/bot-messenger/main/deploy.sh | sh
```

## Features:

1. HTML Parsing;
2. Logging;
3. Usage of external API (Telegram);
4. Tasks scheduling;
5. NoSQL database;
6. Production and Development environments;
7. Docker deployment;
8. Configuration file.

## **TODO**

* Deploy:
    - Pipelines

* New Features:
    - Get `News` section

* Code Improvement:
    - Regular expressions
    - Asynchronous flow
    - Comments and docstrings
    - Use environment variables for production and development status