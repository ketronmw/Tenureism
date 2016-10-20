import os
import pdb
import pickle

import numpy as np
import mysql.connector as mysql
from sklearn import linear_model
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection

import db_info


class PredictCampus:

    def __init__(self, user='root', password='password', verbose=False,
                 table='profs_list_unique', campus='irvine', dept='physics',
                 year=2017):

        self.table = table
        self.user = user
        self.password = password
        self.verbose = verbose
        self.campus = campus
        self.dept = dept
        self.year = year


    def reformat_data(self):

        """ This reads the full SQL file and reformats into a list
        of dictionaries. Each dict contains the departmental averages
        at each campus as a function of time. I'm saving the cumulative
        means to do linear regression on.
        """

        if os.path.isfile('ratings_data.pkl') and self.verbose:
            print 'Overwriting ratings_data.pkl'

        db = mysql.connect(user=self.user, password=self.password)
        sql = db.cursor(buffered=True)
        sql.execute('USE profs')

        # Classify the entire campus -- all the departments. It's so
        # fast to do and it's good to have in the final class.
        sql.execute('SELECT * from profs_ratings_dept_full;')#+
                     #"where campus='{}'".format(self.campus)))

        # Loop through each element & make lists.
        yrs, ratings, depts, campus = [], [], [], []
        for elem in sql:
            yrs.append(int(elem[0]))
            campus.append(str(elem[1]))
            ratings.append(float(elem[3]))
            depts.append(str(elem[4]))

        yrs = np.array(yrs)
        ratings = np.array(ratings)
        depts = np.array(depts)
        campuses = np.array(campus)

        ratings_data = [] # This list will contain dicts for each dept at each campus.
        for kct, campus in enumerate(np.unique(campuses)):
            # For each campus, year & department, compute the average rating.
            for ict, dept in enumerate(np.unique(depts)):
                years_tmp = [] # For each dept, keep track of avg, yr & std.
                ratings_tmp = [] # Re-initialize at each new dept.
                var_tmp = []
                for year in np.unique(yrs):
                    this_yr_dept_ind = (np.where((yrs == year) & (depts == dept)
                                                 & (campuses == campus))[0])
                    if len(this_yr_dept_ind) == 0:
                        continue

                    # Take mean & std and save to list along with this year.
                    ratings_tmp.append(np.mean(ratings[this_yr_dept_ind]))
                    var_tmp.append(np.std(ratings[this_yr_dept_ind]))
                    years_tmp.append(year)

                if len(ratings_tmp) == 0:
                    continue # nothing to save


                # This will be the main data structure. For now I'll do
                # regression for every department.
                years_tmp = np.array(years_tmp)
                var_tmp = np.array(var_tmp)
                ratings_tmp = np.array(ratings_tmp)
                (ratings_data.append({'years':years_tmp,
                                      'ratings':ratings_tmp,
                                      'var':var_tmp,
                                      'dept':dept,
                                      'campus':campus}))

        # Save this data structure so I only have to do that once.
        pickle.dump(ratings_data,open('ratings_data.pkl','wb'))
        if self.verbose:
            print 'Saved ratings_data.pkl'

        return None


    def predict(self):

        """ Actually make some predictions from the data, finally.
        If the ratings_data data structure doesn't exits (I pickled it)
        then this will run self.reformat_data() which will first
        generate it.
        """

        # Check for data file and make it if it doesn't exist.
        if not os.path.isfile('ratings_data.pkl'):
            print "Ratings file doesn't exist -- I'm making a new one..."
            self.reformat_data()
        else:
            ratings_data = pickle.load(open('ratings_data.pkl','r'))


        # Now I'll do linear regression on this self.dept for each campus.
        ict = 0
        campus_names, cols = [], []
        future, future_err = [], []
        for df in ratings_data:
            if self.dept == df['dept']:
                years = df['years']
                ratings = df['ratings']
                campus = df['campus']
                campus_names.append(campus)


                # Do linear regression on cumulative mean of ratings.
                cumul_mean = (np.array([np.sum(ratings[:i])
                                        for i in range(1,len(ratings)+1)]))

                # Train & test indices. Train on 70-80%-ish?
                train = np.where(years <= 2012)[0]
                test = np.where(years > 2012)[0]
                if len(train) <= 1 or len(test) <= 1:
                    continue
                xtrain, ytrain = years[train], cumul_mean[train]
                xtest, ytest = years[test], cumul_mean[test]


                # Train a new instance of the OLS linear model.
                lin = linear_model.LinearRegression()
                lin.fit(xtrain.reshape(-1,1), ytrain)
                y_predict = lin.predict(xtest.reshape(-1,1))


                # Check out the errors.
                diff = ytest - y_predict
                err = np.dot(diff, diff) / len(diff)


                # Show results for each dept.
                if ict == 0:
                    fig = plt.figure()
                    plt1 = fig.add_subplot(111)
                    plt.ion()
                    plt1.set_ylabel('Cumulative Mean Rating', fontsize=15)
                    plt1.set_xlabel('Year', fontsize=15)
                    plt1.set_ylim([5,70])
                    plt1.set_yscale('log')
                    cmap = plt.cm.rainbow
                    nsteps = len(db_info.campus_names)

                    #plt2 = fig.add_subplot(122)
                    #plt2.set_yscale('log')
                    #plt2.set_ylim([20,70])

                col = cmap(ict/float(nsteps))
                cols.append(col)
                plt1.scatter(xtrain, ytrain, color=col)#, alpha=0.5)
                plt1.plot(xtest, y_predict, color=col, linewidth=2, label=campus)
                plt1.fill_between(xtest, y_predict-err, y_predict+err, color=col, alpha=.1)
                ict += 1


                # Now make a prediction for upcoming year and assume errors are similar.
                # Don't plot yet.
                next_year = lin.predict(np.array(self.year).reshape(1,-1))[0]
                future.append(next_year)
                future_err.append(err)

        plt1.legend(campus_names, loc=4)
        plt.show()


        # Second plot is to show the future predictions compared with each campus.
        fig = plt.figure()
        ax = fig.add_subplot(111)
        y = range(len(future))[::-1] # Start first campus at the top
        for i, (f, fe) in enumerate(zip(future, future_err)):
            xy = (f, y[i])
            wid = fe
            hei = 0.5
            ax.add_patch(mpatches.FancyBboxPatch(
                xy, wid, hei,label=campus_names[i],
                boxstyle=mpatches.BoxStyle("Round", pad=0.02), facecolor=cols[i]))
            #plt.plot([f,f], [y[i]-.25,y[i]+.25],color='black',linewidth=3)

        plt.legend(campus_names,loc=2)
        plt.title('Predicted ratings for {} in {}'.format(self.dept, self.year), fontsize=18)
        plt.ylim([-1,10])
        plt.xlim([np.min(future)-np.max(future_err)-4, np.max(future)+np.max(future_err)])

        plt.xlabel('Cumulative Mean Rating', fontsize=15)
        plt.gca().yaxis.set_major_locator(plt.NullLocator()) # turn off y-ticks
        plt.show()

        return None
