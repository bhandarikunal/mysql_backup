#!/usr/bin/env python
# coding: utf-8

###################### Inputs ############################
FREQUENCY_DAYS = 1
# To avoid consdering archives that took long time to backup
# but are recent as old files
BUFFER_DAYS = 1/24 

COMPRESS = True
BACKUP_PATH='/media/kunal/KBServerBkup/mysql'
SYSTEM_DATABASES = ["performance_schema","information_schema","sys",
                    "mysql"]
time_format = "%Y%m%d%H%M%S"

###################### Libraries ############################
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))

from common_py.functions import *

###################### Main program ############################

start_time = time.time()

if not os.path.exists(BACKUP_PATH):
    raise ValueError(f"Backup path [{BACKUP_PATH}] doesn't exist... Exiting...")


# Time to identify old backups
recent_file_time = time.time() - FREQUENCY_DAYS * 24 * 60 * 60
recent_file_time = time.strftime(time_format, time.localtime(recent_file_time))


# Check if there is a backup more recent than above time
current_files = os.listdir(BACKUP_PATH)

new_files = [f for f in current_files
             if re.search(".*_(\\d+)\\..*", f)
                 and re.search(".*_(\\d+)\\..*", f).group(1) >= recent_file_time]

if len(new_files) > 0:
    print(f"mysql_backup.py: Recent backups found [{new_files}]\nExiting...")
    sys.exit(0)


# Databases to backup
databases = set(run_sql("SHOW DATABASES")["Database"]) - set(SYSTEM_DATABASES)

try:
    for db in databases:
        filename = f"{db}_{time.strftime(time_format, time.localtime(time.time()))}"
        filename = os.path.join(BACKUP_PATH, filename)

        print(f"mysql_backup.py: Dumping database [{db}] to file [{filename}.*]")

        if COMPRESS:
            os.system(f"mysqldump --databases {db} | gzip -c > {filename}.gz")
        else:
            os.system(f"mysqldump --databases {db} > {filename}.sql")
except:
    print("mysql_backup.py: Error backing up databases")
    send_email(message = f"Failed to backup mysql databases at [{start_time}]",
              subject = f"kbserver: Failed to backup mysql [{start_time}]")
    raise

print("mysql_backup.py: All databases successfully backed up")


# Delete old backups
old_file_time = time.time() - FREQUENCY_DAYS * 24 * 60 * 60 - BUFFER_DAYS * 24 * 60 * 60
old_file_time = time.strftime(time_format, time.localtime(old_file_time))

old_files = [f for f in current_files
             if re.search(".*_(\\d+)\\..*", f)
                 and re.search(".*_(\\d+)\\..*", f).group(1) < old_file_time]
for f in old_files:
    print(f"mysql_backup.py: Deleting old file [{f}]")
    try:
        os.system(f" rm '{os.path.join(BACKUP_PATH, f)}'")
    except:
        print(f"mysql_backup.py: Error deleting old file [{f}]")


# Final reports to email
finish_time = time.time()
print(f"mysql_backup.py: Time to back up [{(finish_time - start_time) / 3600} hours]")

finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(finish_time))
send_email(message = f"Success in daily mysql backup at [{finish_time}]",
              subject = f"kbserver: Success in daily mysql backup [{finish_time}]")
