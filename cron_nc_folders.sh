#!/bin/bash
# Shell script to read folders properties and write them to file
# Used by cron every hour

sudo du --time --max-depth=1 /var/snap/nextcloud/common/nextcloud/data | sort -nr > /opt/pyTeleMonBot/.data/usage.txt