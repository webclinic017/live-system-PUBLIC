#!/bin/bash

crontab -l > "~/live-system/bin/crons/cron-backup-$(date '+%Y%m%d_%H%M').txt"

cat ~/live-system/bin/crons/cron-static ~/live-system/bin/crons/cron-rotating > ~/live-system/bin/crons/cron-all
crontab ~/live-system/bin/crons/cron-all

