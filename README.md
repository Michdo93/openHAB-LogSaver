# OpenHAB-LogSaver
Save openhab logs into a MariaDB database. You can simply rewrite this code for other databases too. Please consider that it will only read and save the last line of a log file. If you restart openhab the log file should be empty. After each file change the last line will be reread with this program. With this each change should be transmitted into your databse table.

The table looks like:

```
+-------------+-------------+------+-----+---------+----------------+
| Field       | Type        | Null | Key | Default | Extra          |
+-------------+-------------+------+-----+---------+----------------+
| id          | int(11)     | NO   | PRI | NULL    | auto_increment |
| datetime    | datetime    | YES  | MUL | NULL    |                |
| log_level   | varchar(10) | YES  |     | NULL    |                |
| log_event   | varchar(30) | YES  |     | NULL    |                |
| log_message | longtext    | YES  |     | NULL    |                |
+-------------+-------------+------+-----+---------+----------------+
```

## Install

Please make sure that MariaDB is installed:

```
sudo apt update
sudo apt install mariadb-server
sudo mysql_secure_installation
```

After that you have to create an admin user:

```
sudo mariadb
GRANT ALL ON *.* TO 'admin'@'localhost' IDENTIFIED BY 'password' WITH GRANT OPTION;
FLUSH PRIVILEGES;
exit
```

You can now login into the database with:

```
sudo mysql -u root -p
```

If it works you can check the systemd service with:

```
sudo systemctl status mariadb.service
```

With following commands you can start and enable MariaDB:

```
sudo systemctl start mariadb.service
sudo systemctl enable mariadb.service
```

I recommend creating a restricted user for the next step. In my example I use a persistence with openHAB and have created the user `openhab`. The openHAB persistence uses the database `OpenHAB` in my program for storing the openHAB logs I use the database `OpenHAB_LOGS` with this user. But it is optional which users you configure for which database and which rights these users have.

The next step is to install MariaDB for Python 3:


```
sudo apt-get update
sudo apt-get install libmariadb-dev libmariadbclient-dev
pip3 install mariadb
```

And last but not least, you can download the Python code:

```
cd ~
wget https://raw.githubusercontent.com/Michdo93/OpenHAB-LogSaver/main/logsaver.py
sudo chmod +x logsaver.py
```

## Usage

You can run the program with:

```
python3 logsaver.py
```

Please make sure that you have configured the database access in the program accordingly!

To run the program permanently after system startup, you have to create a systemd service:

```
sudo nano /etc/systemd/system/ohlogsaver.service
```

Add the following:

```
[Unit]
Description=openHAB LogSaver service
After=multi-user.target mariadb.service

[Service]
Type=simple
User=<user>
Group=<user>
Restart=always
ExecStart=/usr/bin/python3 /home/<user>/logsaver.py

[Install]
WantedBy=multi-user.target
```

Please make sure that you have to replace `<user>` with the username of your current user!

Then you have to start and enable it:

```
sudo systemctl daemon-reload
sudo systemctl start ohlogsaver.service
sudo systemctl enable ohlogsaver.service
```

### Standard configuration:

```
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
```

### openHAB and HABApp configuration

```
if __name__ == "__main__":
    threads = []

    db_user = "<username>"
    db_password = "<password>"
    host = "<database_ip>"
    port = <port>
    database = "OpenHAB_LOGS"
    location = "/var/log/openhab/"
    habapp_location = "/etc/openhab/habapp/logs/"

    events = OpenHABLogReader(db_user, db_password, host, port, database, "events", location, "events.log")
    openhab = OpenHABLogReader(db_user, db_password, host, port, database, "openhab", location, "openhab.log")
    HABApp_events = OpenHABLogReader(db_user, db_password, host, port, database, "HABApp_events", habapp_location, "HABApp_events.log")
    HABApp = OpenHABLogReader(db_user, db_password, host, port, database, "HABApp", habapp_location, "HABApp.log")

    threads.append(events)
    threads.append(openhab)
    threads.append(HABApp_events)
    threads.append(HABApp)

    for th in threads:
        th.start()

    for t in threads:
        t.join()

    events.disconnect()
    openhab.disconnect()
```

## Custom configuration

### Database connection

As already mentioned you have to configure your own database access:

```
db_user = "<username>"
db_password = "<password>"
host = "<database_ip>"
port = 3306
```

As example the `<username>` could be `openhab` and the `<password>` could be `anonymous`. If you run the database on the same server than your database you can use `127.0.0.1` for `<database_ip>`. As you can see MariaDB runs under the port `3306`. If you use another port you should change that! In the example above we will create and use the database `OpenHAB_LOGS`. If you want to use another database you should rename it! Please be careful: The database will only created if it's not existing.

The variables will be used later.

### Database table

In the constructor you have to use a name for your table. You can define a variable like this:

```
table = "logs"
```

The table `logs` will be created inside your configured database if it is not exsisting! If you want to use another table you should rename `logs`.

Normally openHAB will use the two log files `events.log` and `openhab.log`. So you could use two Threads which will read each of this files and could also create/use two tables. Or if you use HABApp you there are maybe other log files you want to save in your database.

### Log Path

The log path for openHAB 2 and openHAB 3 differs. The path `/var/log/openhab/` is used by openHAB 3 for saving the logs. If you use as example openHAB 2 you want to change the path to `/var/log/openhab2/`. Please make sure that you use a `/` at the end of the path!

```
location = "/var/log/openhab"
```

or

```
location = "/var/log/openhab2"
```

This path may vary if you installed openHAB manually or via Docker. If you are using Docker, you must specify the path to the volume. And of course you can use another path if you are using HABApp.

### How to read a log file

If you want to read a log file you have to run as example:

```
events = OpenHABLogReader(db_user, db_password, host, port, database, "events", location, "events.log")
openhab = OpenHABLogReader(db_user, db_password, host, port, database, "openhab", location, "openhab.log")
```

This are two Threads which could be started. As you can see, some parameters are used twice for the constructors, so the use of variables made sense. If e.g. HABApp is added now, you might want to enter the path for the log data there via another variable or directly in the constructor.

This will read the `/var/log/openhab/events.log` and write its content into the database table `events`. And it will read `/var/log/openhab/openhab.log` and write its content into the database table `openhab`. Of course it is possible that you save it into the same database table.

### Add HABApp Logs

If you want to add as example the HABApp logs to this program for also saving them into the database you have to make sure that the HABApp logs are saved in the same location as the openhab logs or use another object. Please edit the `config.yml` (as example in `/etc/openhab/habapp/`):

```
...
directories:
  logging: /var/log/openhab  # Folder where the logs will be written to
...
```

```
HABApp_events = OpenHABLogReader(db_user, db_password, host, port, database, "HABApp_events", "/etc/openhab/habapp/logs", "HABApp_events.log")
HABApp = OpenHABLogReader(db_user, db_password, host, port, database, "HABApp", "/etc/openhab/habapp/logs", "HABApp.log")
```

Then you have to make sure that HABApp uses the same formatting for saving the logs than openhab. Please edit the `logging.yml` (as example in `/etc/openhab/habapp/`):

```
  HABApp_default:
    class: HABApp.core.lib.handler.MidnightRotatingFileHandler
    filename: '/var/log/openhab/HABApp.log'
    maxBytes: 1_048_576
    backupCount: 3

    formatter: HABApp_format
    level: DEBUG

  EventFile:
    class: HABApp.core.lib.handler.MidnightRotatingFileHandler
    filename: 'HABApp_events.log'
    maxBytes: 1_048_576
    backupCount: 3

    formatter: HABApp_format
    level: DEBUG

  BufferEventFile:
    class: logging.handlers.MemoryHandler
    capacity: 10
    formatter: HABApp_format
    target: EventFile
    level: DEBUG


loggers:
  HABApp:
    level: INFO
    handlers:
      - HABApp_default
    propagate: False

  HABApp.EventBus:
    level: INFO
    handlers:
      - BufferEventFile
    propagate: False

```

