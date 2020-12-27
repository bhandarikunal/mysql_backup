#!/usr/bin/env python
# coding: utf-8

###################### Inputs ############################
FREQUENCY_DAYS = 1
NUM_BACKUPS = 1
COMPRESS = True
IGNORE_TEMP_TABLES = True
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


###################### Functions ############################

def get_temp_tables(db):
    temp_tables = run_sql(f"""SELECT table_name
                              FROM information_schema.tables
                              WHERE table_schema = '{db}'
                              AND table_name REGEXP '(?:^|_)(?:tmp|temp|old)(?:_|$)'""")
    temp_tables = list(temp_tables['TABLE_NAME'])
    return temp_tables


###################### Main program ############################

start_time = time.time()

if not os.path.exists(BACKUP_PATH):
    raise ValueError(f"Backup path [{BACKUP_PATH}] doesn't exist... Exiting...")


# Dates to identify old v/s new backups
run_date = date.today().strftime("%Y%m%d")

# Check if there is a backup for above date
current_files = os.listdir(BACKUP_PATH)

new_file = [f for f in current_files
            if re.search(".*_(\\d+)\\..*", f)
                 and re.search(".*_(\\d+)\\..*", f).group(1)[:8] == run_date]

if len(new_file) > 0:
    print(f"mysql_backup.py: Recent backups found [{new_file}]")
else:
    # Databases to backup
    databases = set(run_sql("SHOW DATABASES")["Database"]) - set(SYSTEM_DATABASES)

    try:
        for db in databases:

            temp_tables_options = " "
            if IGNORE_TEMP_TABLES:
                temp_tables = get_temp_tables(db)

                for t in temp_tables:
                    temp_tables_options = temp_tables_options + f" --ignore-table={t} "

            filename = f"{db}_{time.strftime(time_format, time.localtime(time.time()))}"
            filename = os.path.join(BACKUP_PATH, filename)

            print(f"mysql_backup.py: Dumping database [{db}] to file [{filename}.*]")

            if COMPRESS:
                os.system(f"mysqldump --databases {db} {temp_tables_options} | gzip -c > {filename}.gz")
            else:
                os.system(f"mysqldump --databases {db} {temp_tables_options} > {filename}.sql")
    except:
        print("mysql_backup.py: Error backing up databases")
        send_email(message = f"Failed to backup mysql databases at [{start_time}]",
                  subject = f"kbserver: Failed to backup mysql [{start_time}]")
        raise

    print("mysql_backup.py: All databases successfully backed up")


# Delete old backups
keep_file_min_date = (date.today() + timedelta(days = NUM_BACKUPS - 1)).strftime("%Y%m%d")

old_files = [f for f in current_files
             if re.search(".*_(\\d+)\\..*", f)
                 and re.search(".*_(\\d+)\\..*", f).group(1)[:8] < keep_file_min_date]
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
              subject = f"Success in daily mysql backup [{finish_time}]")
