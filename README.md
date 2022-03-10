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

## Custom configuration

### Database connection

As already mentioned you have to configure your own database access:

```
reader.connect("<username>", "<password>", "<database_ip>", 3306, "OpenHAB_LOGS")
```

As example the `<username>` could be `openhab` and the `<password>` could be `anonymous`. If you run the database on the same server than your database you can use `127.0.0.1` for `<database_ip>`. As you can see MariaDB runs under the port `3306`. If you use another port you should change that! In the example above we will create and use the database `OpenHAB_LOGS`. If you want to use another database you should rename it! Please be careful: The database will only created if it's not existing.

### Database table

With following method

```
reader.createTable("logs")
```

the table `logs` will be created inside your configured database if it is not exsisting! If you want to use another table you should rename `logs`.

### Log Path

The log path is hardcoded because the programm is mainly for openHAB 3. There the path `/var/log/openhab/` is used for saving the logs. If you use as example openHAB 2 you want to change the path to `/var/log/openhab2/`. Please make sure that you use a `/` at the end of the path! You can change the path by changing the string in the `self.location` variable in line 13!

### How to read a log file

If you want to read a log file you have to run as example:

```
reader.readAndSaveLogFile("events.log", "logs")
```

This will read the `/var/log/openhab/events.log` and write its content into your configured database table.

Please consider that the program is only written for using one location where the log files could be found!

If you want to read and save multiple log files you have to use threads like given in following example:

```
Thread(target = reader.readAndSaveLogFile("events.log", "logs")).start()
Thread(target = reader.readAndSaveLogFile("openhab.log", "logs")).start()
```

This should be equivalent to `log:tail` inside the `karaf console` of openhab.

### Add HABApp Logs

If you want to add as example the HABApp logs to this program for also saving them into the database you have to make sure that the HABApp logs are saved in the same location as the openhab logs. Please edit the `config.yml` (as example in `/etc/openhab/habapp/`):

```
...
directories:
  logging: /var/log/openhab  # Folder where the logs will be written to
...
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

After that you have to restart HABApp with `sudo systemctl restart habapp.service`

Then you can add as example two threads for `HABApp.log` and `HABApp_events.log` like following:

```
Thread(target = reader.readAndSaveLogFile("HABApp.log", "log")).start()
Thread(target = reader.readAndSaveLogFile("HABApp_events.log", "logs")).start()
```
