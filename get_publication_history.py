import os
import pdb
import sys

import numpy as np
import mysql.connector as mysql

import db_info
try:
    import scholar as scholar
except:
    raise ImportError('Download scholar.py from '
                      'https://github.com/ckreibich/scholar.py')

class GetPublicationHistory:

    """ This uses the scholar.py code, found at the github link above,
    to get the publication history from each of the professor names
    in the profs_list_unique SQL table statistics. It extracts the number
    of publications per year, the number of citations per year,
    and the total number of publications. These will be the features
    used to do the modeling. 
    """

    def __init__(self, user='root', password='password', verbose=False,
                 table='profs_ratings_dept'):
        self.table = table # need dept for google scholar search.
        self.user = user
        self.password = password
        self.verbose = verbose
        self.pct_found = None

    def get_history(self):

        # Connect to SQL server
        db = mysql.connect(user=self.user, password=self.password)
        sql = db.cursor(buffered=True)

        # Use profs database
        sql.execute('USE profs')

        # Need to remove duplicate names from this table profs_ratings_dept,
        # that was made with get_rating_history.py. There's a prof name for
        # each year there is a rating. But I need the dept name, which I'm
        # getting from rmp.com.
        uniq_cmd = ("""SELECT MIN(name) AS name, campus, dept 
        FROM {} GROUP BY name, campus, dept""".format(self.table))
        sql.execute(uniq_cmd)

        if self.verbose:
            print 'Using professor names in {} with repeats removed.'.format(self.table)


        # Before starting queries, check where we are in the table.
        con_init = mysql.connect(user=self.user, password=self.password)
        sql_ = con_init.cursor(buffered=True)
        sql_.execute('USE profs')
        # Maybe the table profs_pub doesn't exist yet. 
        try:
            sql_.execute("select * from profs_pub order by name desc limit 1;")
            last_line = sql_.fetchall()
            last_entry = str(last_line).split(',')[2].replace(" u'",'').strip().replace("'",'') #yuck
        except:
            last_entry = None
        con_init.close()
        sql_.close()


        # Loop through each prof.
        null_list_ct, i = 0, 0
        for (name, campus, dept) in sql:

            # Continue until we get to the last name in the table.
            if last_entry is not None:
                if name == last_entry:
                    last_entry = None
                i += 1
                print 'skipping {}'.format(name)
                continue

            querier = scholar.ScholarQuerier()
            settings = scholar.ScholarSettings()
            query = scholar.SearchScholarQuery()

            query.set_author(str(name))
            query.set_phrase(str(dept))
            querier.send_query(query)


            if len(querier.articles) > 0:
                null_list_ct = 0 # Returns nothing after Google figures out I'm a bot.

                items = sorted(list(querier.query.attrs.values()), key=lambda item: item[2])
                total_pubs = items[0][0]

                if total_pubs > 10000:
                    print 'total number of publications is too large ({}). '.format(total_pubs)
                    print 'Skipping: {}, {}, {}'.format(str(name), str(dept), str(campus))
                    continue

                # Collect the years of publications, Number, and Citations.
                years, citations = [], []
                for art in querier.articles:
                    try:
                        txt = art.as_txt().encode('ascii','ignore')
                    except:
                        print 'Encoding error...'
                        pdb.set_trace()

                    # Split lines.
                    for line in txt.split('\n'):
                        if 'Year' in line:
                            years.append(line.strip().split(' ')[1])
                        if 'Citations' in line:
                            if 'list' not in line.strip().split(' ')[1]:
                                citations.append(line.strip().split(' ')[1])

                try:
                    citations = np.array(citations, dtype=int)
                    years = np.array(years, dtype=int)
                except:
                    citations = np.zeros(len(years))
                    years = np.zeros(len(years))


                # Remove year duplicates (= number of publications per year!)
                # and add up all citations per year.
                n_pubs, years_unq, citations_per_year = [],[],[]
                for iyr, year in enumerate(np.unique(years)):
                    yr_ind = np.where(years == year)[0]
                    n_pubs.append(len(yr_ind))
                    try:
                        cit_p_y = np.sum(citations[yr_ind])
                    except:
                        cit_p_y = 'NULL'
                    if np.sum(citations) == 0:
                        cit_p_y = 'NULL'

                    citations_per_year.append(cit_p_y)
                    years_unq.append(year)

                # Now put this stuff in a table.
                # Open a new MySQL connection. 
                con2 = mysql.connect(user=self.user, password=self.password)
                sql_buff = con2.cursor(buffered=True)
                sql_buff.execute('USE profs')

                if i == 0:
                    cmd = ('CREATE TABLE profs_pub (year INT, '
                           'campus VARCHAR(15), name VARCHAR(90), dept VARCHAR(50),'
                           'n_pub INT, n_citations INT)')
                    try:
                        sql_buff.execute(cmd)
                        if self.verbose:
                            print 'Created table profs_pub'
                    except:
                        print 'Table "profs_pub" already exitsts, appending...'

                for yr, cit, n_ in zip(years_unq, citations_per_year, n_pubs):
                    #print yr, str(campus), name, dept, n_, cit
                    data_cmd = ("""INSERT INTO profs_pub
                                VALUES ({}, "{}", "{}",
                                "{}", {}, {});""".format(yr,
                                                     str(campus),
                                                     str(name),
                                                     str(dept),
                                                     n_,
                                                     cit))
                    try:
                        sql_buff.execute(data_cmd)
                        con2.commit()
                    except mysql.Error as err:
                        con2.rollback()
                        print 'There was an error with this command (i={}) {}:'.format(i, data_cmd)
                        print 'Error: {}'.format(err)

            else:
                if self.verbose:
                    'There are no results for {} with phrase={}'.format(str(name), str(dept))
                null_list_ct += 1

            if null_list_ct > 1:
                print "Google has blocked your IP address."
                #print 'Try search with {}, for example.'.format(str(name))
                sys.exit(1)

            i += 1
            print i

        pdb.set_trace()
        con2.close(); sql_buff.close()
        return None
