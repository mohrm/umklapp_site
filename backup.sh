#!/bin/bash
rhc ssh umklapp "./app-root/repo/manage.py dumpdata --natural-primary --exclude contenttypes --exclude=auth.Permission" > $1/backups/umklapp-backup-$(date --iso=minutes).json
