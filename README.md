Syncropy backup system
----------------------

Link: https://github.com/henryx/syncropy

Description:
------------

Syncropy is a backup system for remote machines. It is similar of other systems
(e.g. rsnapshot) but it has some differences

Licence:
--------

Syncropy is released under GPLv2 (see GPL.txt for details)

Features:
---------

It use an agent for check and download data.
It manage four distinct datasets (hour, day, week, month).
It save space with hard link creation.
It save data attribute (owner, group, permission, ACL) into database.

Dependencies:
-------------

 - Python 3 or more;
 - Firebird (fdb driver is used);

Installation:
-------------

 - Create database on Firebird;
 - Extract code into a directory;
 - From client directory, copy the client to destination server;
 - Execute client;
 - Execute server.

Usage:
------

Usage is simpliest:

On client:
```
$ python3 sclient.py -p <portnumber>
```
Where `<portnumber>` is the TCP port number where client listen.
For other options, use -h switch.

On server:
```
$ python sserver.py --cfg=<cfgfile> -H # hour backup
$ python sserver.py --cfg=<cfgfile> -D # day backup
$ python sserver.py --cfg=<cfgfile> -W # week backup
$ python sserver.py --cfg=<cfgfile> -M # month backup
```
Where `<cfgfile>` is a file structured like the `backup.cfg` reported in the
archive. For other options, use `-h` switch. Some notes:

 - It is possible to have multiple configuration files, where each file has
   different parameters.
 
 - While database, dataset and and general sections are global, it is possible
   to set any number of sections, one per client.

This is an example of configuration file:
```
[general]
repository = /full/path/to/store/backups
log_file = syncropy-ng.log
log_level = INFO

[database]
host = localhost
port = 3050
user = sysdba
password = masterkey
dbname = syncropy.fdb

[dataset]
hour = 24
day = 6
week = 4
month = 12

[a_server]
type = file
host = localhost
port = 4444
ssl = yes
sslpem = ssl.pem
sslpass = password
path = /full/path/to/backup
acl = yes
pre_command =
post_command =
```

SSL:
---

If you want use the SSL connection, you need:

 - Create SSL certificate with these commands:
```
    openssl genrsa -des3 -out syncropy.key 2048
    openssl req -new -key syncropy.key -out syncropy.csr
    openssl x509 -req -days 365 -in syncropy.csr -signkey syncropy.key -out syncropy.crt
    cat syncropy.key syncropy.crt > syncropy.pem
    openssl gendh >> syncropy.pem
```
  - Launch client with `-S`, `--sslpem` and `--sslpass` options (see `-h` switch for more information).
  - Configure server for use SSL with the same certificate.

Caveats:
--------

Because syncropy use hard links to store its dataset, its use is guaranteed on
linux or unix environments.
