#!/bin/python3
import os
from os import SEEK_END
import sys
import mariadb
from threading import Thread
import time


class OpenHABLogReader(object):

    def __init__(self):
        self.stamp = 0
        self._cached_stamp = 0
        self.location = "/var/log/openhab/"
        self.last_log = ""
        self.connection = None
        self.cursor = None

    def connect(self, user, password, host, port, database):
        try:
            self.connection = mariadb.connect(
                user=user,
                password=password,
                host=host,
                port=port
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

        self.cursor = self.connection.cursor()

        try:
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        except mariadb.Error as e:
            print(f"Error creating Database: {e}")

        try:
            self.cursor.execute(f"USE {database}")
        except mariadb.Error as e:
            print(f"Error using Database: {e}")

    def disconnect(self):
        self.connection.close()

    def createTable(self, tablename):
        try:
            self.cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {tablename} (id INT NOT NULL AUTO_INCREMENT, datetime DATETIME, log_level VARCHAR(10), log_event VARCHAR(30), log_message LONGTEXT, CONSTRAINT AvoidTwiceLogsConstraint UNIQUE (datetime,log_level,log_event,log_message), PRIMARY KEY(id)) ENGINE=InnoDB DEFAULT CHARSET=latin1")
        except mariadb.Error as e:
            print(f"Error creating Table: {e}")

    def readAndSaveLogFile(self, file, tablename):
        while not os.path.exists(self.location + file):
            time.sleep(1)

        while True:
            for filename in os.listdir(self.location):
                if filename == file:
                    while True:
                        if not os.path.exists(self.location + file):
                            time.sleep(1)
                            continue
                        else:
                            stat = os.stat(self.location + file)
                            if(hasattr(stat, 'st_mtime')):
                                self.stamp = stat.st_mtime
                                if stat.st_size == 0:
                                    time.sleep(1)
                                    break
                                if self.stamp > self._cached_stamp:
                                    self._cached_stamp = self.stamp
                                    with open((self.location + file), "r") as f:
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

                                    sql_command = (f"INSERT INTO {tablename} "
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



if __name__ == "__main__":
    reader = OpenHABLogReader()

    reader.connect("<user>", "<password>", "<database_ip>", 3306, "OpenHAB_LOGS")
    reader.createTable("logs")

    Thread(target=reader.readAndSaveLogFile("events.log", "logs")).start()
    Thread(target=reader.readAndSaveLogFile("openhab.log", "logs")).start()

    reader.disconnect()
