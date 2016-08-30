#!/usr/bin/python

""" This script generates MySQL tables from the 10 different .csv files
in .data/. After the 10 .csv files are downloaded to .data (which this
script does), it concatenates them and then produces a uniqe table with
duplicates removed. Also generates tables with list of professors who have
been at the same university for > or < 3,4,5,8,10 years.

$ python make_sql_tables.py user password

Ketron 8/2016
"""

from sys import argv
import os

import mysql.connector as mysql
try:
    import urllib
except:
    raise ImportError('urllib needs to be installed.')

import db_info


# First the data need to be downloaded to .data/ directory.
if not os.path.exists('.data/'):
    os.makedirs('.data/')

myurl = 'http://herschel.uci.edu/ketron/tenureism_data/'
print 'Downloading data from ' + myurl
for campus in db_info.campus_names:
    fname = 'ucpay.globl.org.' + campus + '.csv'
    urllib.urlretrieve(myurl + fname, '.data/' + fname)
    print 'Saving ./data/' + fname + ' ...'


# SQL login info.
try:
    this_name, user_name, password = argv
except:
    user_name, password = 'root', 'password'

print 'Using these login params for MySQL:' 
print 'User: {}'.format(user_name)
print 'Password: {}'.format(password)

# Connect to mysql server.
connect = mysql.connect(user=user_name, password=password)
mysql_con = connect.cursor(buffered=True)

# Make profs database if one doesn't exist. Then use it.
mysql_con.execute('CREATE DATABASE IF NOT EXISTS profs;')
mysql_con.execute('USE profs')
print 'Using database: profs.'

# Create single table from all the *.csv files.
cmd = ('CREATE TABLE ucpay_profs (year INT, campus VARCHAR(15), '+
       'last_name VARCHAR(40), first_name VARCHAR(50), title VARCHAR(50), '+
       'base FLOAT, overtime FLOAT, extra FLOAT, gross FLOAT);')
try:
    mysql_con.execute(cmd)
except:
    mysql_con.execute('DROP TABLE ucpay_profs;')
    mysql_con.execute(cmd)

for campus in db_info.campus_names:
    cmd = ("LOAD DATA LOCAL INFILE '.data/ucpay.globl.org."+campus+".csv' " +
           "INTO TABLE ucpay_profs FIELDS TERMINATED BY ',' IGNORE 1 LINES;")
    mysql_con.execute(cmd)

print 'Created table ucpay_profs, in profs database, of all *.csv files.'


# Remove duplicates from ucpay_profs and save to new table.
# GROUP command will remove duplicates.
try:
    cmd = ('CREATE TABLE profs_list_unique AS '+
                      'SELECT last_name, first_name, '+
                      'campus FROM ucpay_profs '+
                      'GROUP BY last_name, first_name, campus;')
    mysql_con.execute(cmd)
except:
    mysql_con.execute('DROP TABLE profs_list_unique;')
    mysql_con.execute(cmd)

print 'Created table with all unique rows as profs_list_unique.'

# Create table where there are > N occurances of given prof.
N = [3,4,5,8,10]
for n in N:
    try:
        cmd = ('CREATE TABLE profs_list_over'+str(n)+' AS SELECT last_name, '+
               'first_name,campus, COUNT(*) AS occurences FROM ucpay_profs '+
               'GROUP BY last_name, first_name, campus HAVING COUNT(*)>' +
               str(n)+';')
        mysql_con.execute(cmd)
    except:
        mysql_con.execute('DROP TABLE profs_list_over'+str(n)+';')
        mysql_con.execute(cmd)

    print 'Created table: profs_list_over' + str(n)


# Do the inverse of above -- keep where profs < N occurances.
for n in N:
    try:
        cmd = ('CREATE TABLE profs_list_under'+str(n)+' AS SELECT last_name, '+
               'first_name,campus, COUNT(*) AS occurences FROM ucpay_profs '+
               'GROUP BY last_name, first_name, campus HAVING COUNT(*)>' +
               str(n)+';')
        mysql_con.execute(cmd)
    except:
        mysql_con.execute('DROP TABLE profs_list_under'+str(n)+';')
        mysql_con.execute(cmd)

    print 'Created table: profs_list_under' + str(n)
