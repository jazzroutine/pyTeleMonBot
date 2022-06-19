
# <p align="center">pyTeleMonBot

<p align="center">Simple Telegram bot for server monitoring made with <a href="https://github.com/eternnoir/pyTelegramBotAPI">pyTelegramBotAPI</a>.</p>
<p align="center">Initially made for <a href="https://matrix.org/docs/projects/server/synapse">Matrix Synapse</a> and <a href="https://nextcloud.com/">NextCloud</a> servers.</p>

## Contents

* [Getting started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Project folder](#project-folder)
  * [Requirements and virtualenv](#requirements-and-virtualenv)
  * [Service creation](#service-creation)
  * [Matrix DB configuration](matrix-db-configuration)
  * [NextCloud configuration](nextcloud-configuration)

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




