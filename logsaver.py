#!/bin/python3
import threading
import os
from os import SEEK_END
import sys
import mariadb
import time

class OpenHABLogReader(threading.Thread):

    def __init__(self, user:str, password:str, host:str, port:int, database:str, tablename:str, location:str, file:str):
        threading.Thread.__init__(self)
        self.threadID = threading.current_thread().ident
        self.stamp = 0
        self._cached_stamp = 0
        self.location:str = location
        self.file:str = file
        self.last_log = ""
        self.connection = None
        self.cursor = None
        self.user:str = user
        self.password:str = password
        self.host:str = host
        self.port:str = port
        self.database:str = database
        self.tablename:str = tablename

    def __connect(self):
        try:
            self.connection = mariadb.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

        self.cursor = self.connection.cursor()

        try:
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        except mariadb.Error as e:
            print(f"Error creating Database: {e}")

        try:
            self.cursor.execute(f"USE {database}")
        except mariadb.Error as e:
            print(f"Error using Database: {e}")

    def disconnect(self):
        self.connection.close()

    def __createTable(self):
        try:
            self.cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {self.tablename} (id INT NOT NULL AUTO_INCREMENT, datetime DATETIME, log_level VARCHAR(10), log_event VARCHAR(30), log_message LONGTEXT, CONSTRAINT AvoidTwiceLogsConstraint UNIQUE (datetime,log_level,log_event,log_message), PRIMARY KEY(id)) ENGINE=InnoDB DEFAULT CHARSET=latin1")
        except mariadb.Error as e:
            print(f"Error creating Table: {e}")

    def __readAndSaveLogFile(self):
        while not os.path.exists(self.location + self.file):
            time.sleep(1)

        while True:
            for filename in os.listdir(self.location):
                if filename == self.file:
                    while True:
                        if not os.path.exists(self.location + self.file):
                            time.sleep(1)
                            continue
                        else:
                            stat = os.stat(self.location + self.file)
                            if(hasattr(stat, 'st_mtime')):
                                self.stamp = stat.st_mtime
                                if stat.st_size == 0:
                                    time.sleep(1)
                                    break
                                if self.stamp > self._cached_stamp:
                                    self._cached_stamp = self.stamp
                                    with open((self.location + self.file), "r") as f:
                                        read = f.readlines()

                                    if len(read) < 0:
                                        time.sleep(1)
                                        continue

                                    self.last_log = read[-1]

                                    print(self.last_log)

                                    splitted = self.last_log.replace(" ]", "]").split()
                                    print(splitted)
                                    datetime = splitted[0] + " " + splitted[1]
                                    log_level = splitted[2][1:].replace("]", "")
                                    log_event = splitted[3].rsplit(
                                        ".", 1)[-1].replace("]", "")
                                    log_message = ""

                                    for i in range(5, len(splitted), 1):
                                        log_message += splitted[i] + " "

                                    log_message = log_message.replace("'", "")

                                    sql_command = (f"INSERT INTO {self.tablename} "
                                                   "(`datetime`, `log_level`, `log_event`, `log_message`) "
                                                   "VALUES(?, ?, ?, ?) ")

                                    params = (datetime, log_level,
                                              log_event, log_message)

                                    try:
                                        self.cursor.execute(
                                            sql_command,
                                            params
                                        )
                                    except mariadb.Error as e:
                                        print(
                                            f"Error inserting Values into Table: {e}")

                                    try:
                                        self.connection.commit()
                                    except mariadb.Error as e:
                                        print(f"Error commiting insert values: {e}")
                            else:
                                continue
                        continue

    def run(self):
        self.__connect()
        self.__createTable()
        self.__readAndSaveLogFile()

if __name__ == "__main__":
    threads = []

    db_user = "<username>"
    db_password = "<password>"
    host = "<database_ip>"
    port = <port>
    database = "OpenHAB_LOGS"
    location = "/var/log/openhab/"

    events = OpenHABLogReader(db_user, db_password, host, port, database, "events", location, "events.log")
    openhab = OpenHABLogReader(db_user, db_password, host, port, database, "openhab", location, "openhab.log")

    threads.append(events)
    threads.append(openhab)

    for th in threads:
        th.start()

    for t in threads:
        t.join()

    events.disconnect()
    openhab.disconnect()
