import os

import mysql.connector as mysql
try:
    import urllib
except:
    raise ImportError('urllib needs to be installed.')

import db_info


class MakeSQLTables:

    """ This script generates MySQL tables from the 10 different .csv files
    in .data/. After the 10 .csv files are downloaded to .data (which this
    module does), it concatenates them and then produces a uniqe table with
    duplicates removed. Also generates tables with list of professors who have
    been at the same university for > or < 3,4,5,8,10 years. Edit N in db_info.py
    to change that.

    If you have a .data/ directory in your current working directory, this
    class will assume you've generated the tables already and it will do
    nothing.
    """

    def __init__(self, user='root', password='password', verbose=False):
        self.user = user
        self.password = password
        self.verbose = verbose

    def make_tables(self):
        # First the data need to be downloaded to .data/ directory.
        # If the .data directory exists, I assume you have already downloaded
        # the necessary dataset and make the MySQL tables. 

        if not os.path.exists('.data/'):
            os.makedirs('.data/')

            myurl = 'http://herschel.uci.edu/ketron/tenureism_data/'
            print 'Downloading data from ' + myurl
            for campus in db_info.campus_names:
                fname = 'ucpay.globl.org.' + campus + '.csv'
                urllib.urlretrieve(myurl + fname, '.data/' + fname)
                print 'Saving ./data/' + fname + ' ...'


            # SQL login 
            print 'Using these login params for MySQL:' 
            print 'User: {}'.format(self.user)
            print 'Password: {}'.format(self.password)

            # Connect to mysql server.
            connect = mysql.connect(user=self.user, password=self.password)
            mysql_con = connect.cursor(buffered=True)

            # Make profs database if one doesn't exist. Then use it.
            mysql_con.execute('CREATE DATABASE IF NOT EXISTS profs;')
            mysql_con.execute('USE profs')
            print 'Using database: profs.'

            # Create single table from all the *.csv files.
            cmd = ('CREATE TABLE ucpay_profs (year INT, campus VARCHAR(15), '+
                   'last_name VARCHAR(40), first_name VARCHAR(50), title '+
                   'VARCHAR(50), base FLOAT, overtime FLOAT, extra FLOAT, '+
                   'gross FLOAT);')
            try:
                mysql_con.execute(cmd)
            except:
                mysql_con.execute('DROP TABLE ucpay_profs;')
                mysql_con.execute(cmd)

                for campus in db_info.campus_names:
                    cmd = ("LOAD DATA LOCAL INFILE '.data/ucpay.globl.org."+
                           campus+".csv' INTO TABLE ucpay_profs FIELDS "+
                           "TERMINATED BY ',' IGNORE 1 LINES;")
                    mysql_con.execute(cmd)

            if self.verbose:
                print ('Created table ucpay_profs, in profs database, '+
                       'of all *.csv files.')


            # Remove duplicates from ucpay_profs and save to new table.
            # GROUP command will remove duplicates.
            cmd = ('CREATE TABLE profs_list_unique AS '+
                   'SELECT last_name, first_name, '+
                   'campus FROM ucpay_profs '+
                   'GROUP BY last_name, first_name, campus;')
            try:
                mysql_con.execute(cmd)
            except:
                mysql_con.execute('DROP TABLE profs_list_unique;')
                mysql_con.execute(cmd)

            if self.verbose:
                print 'Created table with all unique rows as profs_list_unique.'


            # Create table where there are > N occurances of given prof.
            for n in db_info.N:
                cmd = ('CREATE TABLE profs_list_over'+str(n)+' AS SELECT '+
                       'last_name, first_name,campus, COUNT(*) AS occurences '+
                       'FROM ucpay_profs GROUP BY last_name, first_name, '+
                       'campus HAVING COUNT(*)>'+str(n)+';')
                try:
                    mysql_con.execute(cmd)
                except:
                    mysql_con.execute('DROP TABLE profs_list_over'+str(n)+';')
                    mysql_con.execute(cmd)

                if self.verbose:
                    print 'Created table: profs_list_over' + str(n)


            # Do the inverse of above -- keep where profs < N occurances.
            for n in db_info.N:
                cmd = ('CREATE TABLE profs_list_over'+str(n)+' AS SELECT '+
                       'last_name, first_name,campus, COUNT(*) AS occurences '+
                       'FROM ucpay_profs GROUP BY last_name, first_name, '+
                       'campus HAVING COUNT(*)<'+str(n)+';')
                try:
                    mysql_con.execute(cmd)
                except:
                    mysql_con.execute('DROP TABLE profs_list_under'+str(n)+';')
                    mysql_con.execute(cmd)

                if self.verbose:
                    print 'Created table: profs_list_under' + str(n)

        else:
            # Don't do anything since .data/ directory already exists.
            if self.verbose:
                print ('Not downloading data or generating MySQL tables -- '+
                       '.data/ dir already exists.')

        return True
