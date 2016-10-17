import os
import pdb

import numpy as np
import mysql.connector as mysql

import db_info


class PredictCampus:

    def __init__(self, user='root', password='password', verbose=False,
                 table='profs_list_unique', campus='irvine', dept=False):
        self.table = table
        self.user = user
        self.password = password
        self.verbose = verbose
        self.pct_found = None
        self.campus = campus
        self.dept = dept

    def predict(self):

        """ Actually make some predictions from the data, finally."""

        db = mysql.connect(user=self.user, password=self.password)
        sql = db.cursor(buffered=True)
        sql.execute('USE profs')

        # Classify the entire campus -- all the departments. It's so
        # fast to do and it's good to have in the final class.
        (sql.execute('SELECT * from profs_ratings_dept_full '+
                     "where campus='{}'".format(self.campus)))

        # Loop through each element & make lists.
        yrs, ratings, depts = [], [], []
        for elem in sql:
            yrs.append(int(elem[0]))
            ratings.append(float(elem[3]))
            depts.append(str(elem[4]))

        yrs = np.array(yrs)
        ratings = np.array(ratings)
        depts = np.array(depts)


        # For each year & department, compute the average rating.
        ratings_data = [] # This list will contain dicts for each dept.
        for dept in np.unique(depts):
            years_tmp = [] # For each dept, keep track of avg, yr & std. 
            ratings_tmp = [] # Re-initialize for each dept.
            var_tmp = []
            for year in np.unique(yrs):
                this_yr_dept_ind = np.where((yrs == year) & (depts == dept))[0]
                if len(this_yr_dept_ind) == 0:
                    continue
                # Take mean & std and save to list along with this year.
                ratings_tmp.append(np.mean(ratings[this_yr_dept_ind]))
                var_tmp.append(np.std(ratings[this_yr_dept_ind]))
                years_tmp.append(year)


            # This will be my main data structure to do learning with.
            (ratings_data.append({'years':years_tmp,
                                  'ratings':ratings_tmp,
                                  'var':var_tmp,
                                  'dept':dept}))

        pdb.set_trace()

        #if self.dept:




        return None
