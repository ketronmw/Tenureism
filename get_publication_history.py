import os
import pdb

import numpy as np
import mysql.connector as mysql

import db_info
try:
    import scholar
except:
    raise ImportError('Download scholar.py from '
                      'https://github.com/ckreibich/scholar.py')

class GetPublicationHistory:

    """ This uses the scholar.py code, found at the github link above,
    to get the publication history from each of the professor names
    in the profs_list_unique SQL tablestatistics. It extracts the number
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

        # Loop through each prof.
        for (name, campus, dept) in sql:

            querier = scholar.ScholarQuerier()
            settings = scholar.ScholarSettings()
            query = scholar.SearchScholarQuery()

            query.set_author(str(name))
            query.set_phrase(str(dept))
            querier.send_query(query)

            if len(querier.articles) > 0:

                items = sorted(list(querier.query.attrs.values()), key=lambda item: item[2])
                total_pubs = items[0][0]

                if total_pubs > 10000:
                    print 'total number of publications is too large ({}). '.format(total_pubs)
                    print 'Skipping: {}, {}, {}'.format(str(name), str(dept), str(campus))
                    continue

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

                    # Remove year duplicates (= number of publications!) and add
                    # up all citations per year.

            else:
                if self.verbose:
                    'There are no results for {} with phrase={}'.format(str(name, str(dept)))

            pdb.set_trace()

        return None
