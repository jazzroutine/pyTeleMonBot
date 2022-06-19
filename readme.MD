
# pyTeleMonBot

Simple Telegram bot for server monitoring made with <a href="https://github.com/eternnoir/pyTelegramBotAPI">pyTelegramBotAPI</a>.

Initially made for <a href="https://matrix.org/docs/projects/server/synapse">Matrix Synapse</a> and <a href="https://nextcloud.com/">NextCloud</a> servers with secure access to all bot functions.

## Contents

* [Getting started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Project folder](#project-folder)
  * [Requirements and virtualenv](#requirements-and-virtualenv)
  * [Service creation](#service-creation)
  * [Matrix DB configuration](#matrix-db-configuration)
  * [NextCloud configuration](#nextcloud-configuration)
* [General use](#general-use)
  * [First start](#first-start)
  * [Inline commands](#inline-commands)
  * [Monitoring jobs](#monitoring-jobs)
* [Final thoughts](#final-thoughts)

## Getting started

This bot is tested with Python 3.6-3.10 in virtualenv.
You will find all installation instructions for Ubuntu server below(tested on Ubuntu 18 and 20). 


### Prerequisites

First of all, we need Python 3.6+, pip3, virtualenv and libpq-dev.
Usually Python and Pip3 is already installed on Ubuntu, so we will need to add remaining packages.

Installation of virtualenv using system-wide pip3:
```
$ sudo pip3 install virtualenv
$ sudo apt-get install libpq-dev
```

All additional prerequisites will be installed inside virtualenv enviroment.

We also need dedicated local user for bot operations:
```
$ sudo useradd pyTeleMonBot
$ sudo passwd pyTeleMonBot
```

Additionally, we need to create local group to ease permissions management and future changes in bot configuration without sudo.

Group creation:
```
$ sudo groupadd pyTeleMonBot_users
$ sudo usermod -a -G pyTeleMonBot_users pyTeleMonBot
$ sudo usermod -a -G pyTeleMonBot_users %USER%  # don't forget to add yourself to the group!
```

**We need to re-login to make the new group membership active!**



### Project folder

For main project folder we will use `/opt/pyTeleMonBot`

```
$ sudo mkdir /opt/pyTeleMonBot
```
Additionally we need to create data folder for future use:
```
$ sudo mkdir /opt/pyTeleMonBot/.data
```

After folders creation, let's set correct security permissions:
```
$ sudo chown -R pyTeleMonBot /opt/pyTeleMonBot
$ sudo chgrp -R pyTeleMonBot_users /opt/pyTeleMonBot
$ sudo chmod -R 775 /opt/pyTeleMonBot
```

### Requirements and virtualenv

Let's initialize virtualenv in our project folder:
```
$ cd /opt/pyTeleMonBot
$ virtualenv .venv  # optionally we can set Python version with `-p` 
```

Now we can activate it:
```
$ source /opt/pyTeleMonBot/.venv/bin/activate
```

While inside virtualenv, we have to install additional requirements for bot to work:
```
$ pip3 install pyTelegramBotAPI
$ pip3 install tabulate
$ pip3 install psycopg2-binary
$ pip3 install psutil
$ pip3 install aioschedule
$ pip3 install aiohttp
$ pip3 install asyncio
$ pip3 install python-dotenv
$ pip3 install mysql-connector-python
```

Now we can deactivate it:
```
$ deactivate
```

### Service creation

Let's create a simple service for our project:
```
$ sudo nano /etc/systemd/system/pyTeleMonBot.service
```

pyTeleMonBot.service:
```
#Systemd unit file for pyTeleMonBot
[Unit]
Description=pyTeleMonBot Monitoring Service
After=multi-user.target

[Service]
Type=simple

ExecStart=/bin/bash /opt/pyTeleMonBot/service_run.sh
ExecStop=/bin/kill -15 $MAINPID

User=pyTeleMonBot
Group=pyTeleMonBot
UMask=0007
RestartSec=10
Restart=always

[Install]
WantedBy=multi-user.target
```

System systemctl reload:
```
$ sudo systemctl daemon-reload
```

Service auto-start activation:
```
$ sudo systemctl enable pyTeleMonBot.service
```

Starter shell script creation:
```
$ nano /opt/pyTeleMonBot/service_run.sh
``` 

service_run.sh:
```
#!/bin/bash
# Shell wrapper script to activate virtual environment
# Used in /etc/systemd/system/pyTeleMonBot.service

source /opt/pyTeleMonBot/.venv/bin/activate
python3 /opt/pyTeleMonBot/main.py
```

Make executable:
```
$ sudo chmod +x /opt/pyTeleMonBot/service_run.sh
```

### Matrix DB configuration

We need to configure local Synapse Postgres DB and create local read-only user for bot to use.

To connenct:
```
$ sudo -u postgres psql
```

Let's change DB connection to Synapse database:
```
\c synapse
```

User creation and right assigment:
```
CREATE ROLE pyTeleMonBot_ro_user LOGIN PASSWORD 'PASSWORD'; #  don't forget to set password!
GRANT CONNECT ON DATABASE synapse TO pyTeleMonBot_ro_user;
GRANT USAGE ON SCHEMA public TO pyTeleMonBot_ro_user;
GRANT SELECT ON public."users" TO pyTeleMonBot_ro_user;
\q
```

Now we have **pyTeleMonBot_ro_user** with right to read users table from local Synapse DB.


### NextCloud configuration

I my case, I have NextCloud in SNAP container and it's very complicated to work with NextCloud DB directly. So I made simple cron job to make NextCloud folder listing and put it in pyTeleMonBot .data folder.

Let's create shell script for cron to use:
```
$ nano /opt/pyTeleMonBot/cron_audit_folders.sh
```

cron_audit_folders.sh:
```
#!/bin/bash
# Shell script to read folders properties and write them to file
# Used by cron every hour

sudo du --time --max-depth=1 /var/snap/nextcloud/common/nextcloud/data | sort -nr > /opt/pyTeleMonBot/.data/usage.txt
```

This script runs under sudo, so make sure your Ubuntu is ready for this. 

Don't forget to make it executable:
```
$ sudo chmod +x /opt/pyTeleMonBot/cron_audit_folders.sh
```

Now let's make new cron job and set it to run our script every hour:
```
$ sudo crontab -e
```

Add this to the end:
```
0 */1 * * * /opt/pyTeleMonBot/cron_audit_folders.sh
```

## General use

Bot's `main.py` file basicly consists of two major parts: inline commands handlers and asyncio monitoring jobs. 
But before that, let's fill out configuration file and start bot service.

### First start

Before service start, you need to change `.env` file and fill it with your configuration:
* API_KEY - you bot API key from BotFather
* LIST_OF_USERS - List of user who can send inline commands to bot
* LIST_OF_USERS_CHATS - list of chats ID to sent bot's monitoring messages 

* DB_1_PASS - Matrix Synapse read only user password

Without your Telegram account and chat ID to appropriate lists, you will be unable to interact with the bot. 

Now we can start the bot:
```
$ sudo service pyTeleMonBot start
```

### Inline commands

Beside form /start initialization command, all other commands are very self-explanatory:

* /status - Ask all monitored services for their status. 
* /server - Basic server OS info

* /matrix - List of Matrix users and their registration date in UTC+3 timezone
* /nextcloud - List of NextCloud users based on service folder tree and their used space 

* /id - current chat ID
* /bot_users - List of users who can send commands to bot
* /help - Help message

### Monitoring jobs

This is the most complicated part. 

Bot is working in asynchronous mode and beside inline handlers, it's containing dedicated jobs to monitor internal services.

Job list:
* monitor_service1 - Matrix main web page check (every 5 minutes)
* monitor_service2 - Matrix main python service check (every 5 minutes)
* monitor_service3 - Matrix postgres DB connection check (every 5 minutes)
* monitor_service4 - Matrix postgres DB new user alert (every 2 minutes)
* monitor_service5 - NextCloud main web page check (every 5 minutes)
* monitor_service10 - Recent server reboot check (every 5 minutes)

Additionally `monitor_service4` exports Matrix users in to local file for further use in external monitoring. 


## Final thoughts

Initially, this project was created only for the one service monitoring purposes, but over time, has grown into a rather large bot with different ways of interacting.

My Python skill are very limited and I'm sure there are a lots of poor code examples here, but I did my best.
I hope this project will help someone to monitor their servers and services, or be just a starting point to create your own bot for different purposes.

And sorry for my terrible English, it's not my native language, but I hope this readme and code comments were readable.

**Special thanks to:**

* <a href="https://febimudiyanto.medium.com/">Febi Mudiyanto</a> from Medium for <a href="https://python.plainenglish.io/monitoring-server-with-telegram-bot-and-python-b39d0a384fab">his great article</a> about pyTelegramBotAPI monitoring bot!
* <a href="https://github.com/eternnoir">eternnoir</a> for <a href="https://github.com/eternnoir/pyTelegramBotAPI">pyTelegramBotAPI</a> very straightforward documentation with lots of examples!
