import os
import pdb
import pickle

import tempfile
import numpy as np
from sklearn import linear_model
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from flask import Flask, render_template, request, redirect

import db_info


app = Flask(__name__)

@app.route('/')
def main():
    return redirect('/index')

@app.route('/index', methods=['GET','POST'])
def index():
    return render_template('index.html')

@app.route('/figures',methods=['POST'])
def predict_campus():

    """ Takes a department input from a user and performs
    linear regression for that dept over all campuses. See
    https://github.com/ketronmw/Tenureism.
    """

    # Load ratings and get dept from user input.
    ratings_data = pickle.load(open('ratings_data.pkl','r'))
    dept = request.form['departmentText'].lower()
    #dept = 'biology'

    # Do some linear regression!
    year = datetime.now().year + 1 # do prediction for next year!
    ict = 0
    campus_names, cols = [], []
    future, future_err = [], []
    for df in ratings_data:
        if dept == df['dept']:
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
                #plt.ion()
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
            next_year = lin.predict(np.array(year).reshape(1,-1))[0]
            future.append(next_year)
            future_err.append(err)


    plt1.legend(campus_names, loc=4)
    f = 'static/tmp1.png'
    fig.savefig(f)
    plotPng1 = 'tmp1.png'


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
    plt.title('Predicted ratings for {} in {}'.format(dept, year), fontsize=18)
    plt.ylim([-1,10])
    plt.xlim([np.min(future)-np.max(future_err)-4, np.max(future)+np.max(future_err)])
    plt.xlabel('Cumulative Mean Rating', fontsize=15)
    plt.gca().yaxis.set_major_locator(plt.NullLocator()) # turn off y-ticks
    f = 'static/tmp2.png'
    fig.savefig(f)
    plotPng2 = 'tmp2.png'

    return render_template('figures.html', plotPng1=plotPng2, plotPng2=plotPng1)


if __name__ == '__main__':
    app.debug=True
    app.run()
#    port=int(os.environ.get("PORT",5000))
#    if port==5000 :
#	app.run(port=port,host='0.0.0.0')
#    else :
#	app.run(port=port)

