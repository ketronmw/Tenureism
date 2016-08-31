import os
import pdb

from datetime import datetime

import db_tables
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
    3) Scrape *google scholar* to get publication history. Also
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
    verbose -- print messages throughout (default True).


    Usage:
    # For Chemistry at San Diego:
    from tenureism import Tenureism
    next_year = Tenureism(campus='san_diego', dept='chemistry', year=2016)
    next_year.predict()

    # For the entire santa barbara campus in 2017:
    sb = Tenureism(campus='santa_barbara', year=2017)
    sb.predict()
    """

    def __init__(self, campus='irvine', dept='physics', year=None, user='root',
                 password='password', tables_exist=False, verbose=True):

        if campus.lower() not in db_info.campus_names:
            print 'You have to choose from one of the existing campuses:'
            raise TypeError(db_info.campus_names)
        self.campus = campus.lower()
        self.dept = dept.lower()
        self.user= user
        self.password = password
        self.verbose = verbose

        now = datetime.now()
        if now.month >= 8:
            # If it is August or later, the next academic year is this year + 1.
            self.year = now.year + 1
        else:
            # If it is pre-August, the next academic year is this year.
            self.year = now.year

        # 1) Download the csv files & make initial SQL tables.
        sql_table0 = (MakeSQLTables(user=self.user, password=self.password,
                                    verbose=self.verbose))
        sql_tables0.make_tables()

        # 2) Scrape ratemyprofessors.com
        ratings = (GetRatingHistory(user=self.user, password=self.password,
                                    verbose=self.verbose))
        ratings.get_history()

        # 3) Scrape google scholar
        #pub = (GetPubHistory(user=self.user, password=self.password,
        #                     verbose=self.verbose))
        #pub.get_history()

        # All the Tables should now be set up and we can make predictions.

    def predict(self):

        """ All of the data tables should be set up now. Just call
        the predictive function on this dataset.
        """


