import os
import pdb

from datetime import datetime

import db_info
from make_sql_tables import MakeSQLTables
from get_rating_history import GetRatingHistory
from get_publication_history import GetPublicationHistory
from predict_campus import PredictCampus

class Tenureism:

    """ Predict one UC campus+dept performance for some upcoming academic year.

    The steps of this main module from the beginning to the end are:
    1) Download dataset and generate MySQL tables with make_sql_tables.py
       If you have a .data/ directory in your current working directory
       the code assumes you've made the necessary SQL tables already.
    2) Scrape ratemyprofessors.com with get_rating_history.py for
       every professor employed at the UC. This takes a while -- there
       are around 20k unique names in this dataset.
    3) Scrape google scholar to get publication history. Also
       takes a while. Both ratings and pub history data are saved
       as SQL tables and only need to be run once.
    4) Make some predictions about some inputted academic year.


    Keyword arguments for class instance:
    user -- user name for local MySQL login (default 'root').
    password -- password for your local MySQL login (default 'password').
    campus -- choose between one of the 10 UC campuses (default 'irvine').
    dept -- Department you want to know the future "quality" of (default
            is None and the code will return results for entire campus).
    year -- choose some year in the future. If none is input, the default
            is to choose the next academic year.
    verbose -- print messages throughout (default False).


    Usage:
    # To compare biology between campuses for 2017:
    from tenureism import Tenureism
    next_year = Tenureism('biology')
    """

    def __init__(self, dept, campus='irvine', year=None, user='root',
                 password='password', tables_exist=False, verbose=False):

        if dept is None:
            raise TypeError('You need to choose a department!')

        campus = campus.lower().replace(' ','_')
        if campus.lower() not in db_info.campus_names:
            print 'You have to choose from one of the existing campuses:'
            raise TypeError(db_info.campus_names)

        self.campus = campus.lower()
        self.dept = dept.lower()
        self.user= user
        self.password = password
        self.verbose = verbose
        self.year = year

        now = datetime.now()
        if not self.year:
            # No input from user.
            self.year = now.year + 1
        else:
            # Input from user.
            if self.year <= now.year:
                raise ValueError('Input year should not be in the past.')


        # Start the generation of the final table:
        # 1) Download the csv files & make initial SQL tables.
        sql_table0 = (MakeSQLTables(user=self.user, password=self.password,
                                    verbose=self.verbose))
        sql_table0.make_tables()


        # 2) Scrape ratemyprofessors.com
        ratings = (GetRatingHistory(user=self.user, password=self.password,
                                    verbose=self.verbose))
        ratings.get_history()
 

        # 3) Scrape google scholar.
        # Google is flagging me as a bot -- skip this for now.
        #pub = (GetPublicationHistory(user=self.user, password=self.password,
        #                     verbose=self.verbose))
        #pub.get_history()


        # 4) Make some predictions.
        predictions = (PredictCampus(user=self.user, password=self.password,
                                     verbose=self.verbose, campus=self.campus,
                                     year=self.year, dept=self.dept))
        predictions.predict()


        return None
