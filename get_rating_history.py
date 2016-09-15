import os
import pdb
import re

import numpy as np
import mechanize
import requests
import json
import mysql.connector as mysql
from bs4 import BeautifulSoup
from lxml import html

import db_info

class GetRatingHistory:

    """ Reads SQL table with a list of unique professor names and
    scrapes ratemyprofessor.com for each prof.

    Usage:
    from get_rating_history import GetRatingHistory
    ratings = GetRatingHistory()
    ratings.get_history()

    If the rmp table already exists, this does nothing.
    """

    def __init__(self, user='root', password='password', verbose=False,
                 table='profs_list_unique'):
        self.table = table
        self.user = user
        self.password = password
        self.verbose = verbose
        self.pct_found = None

    def capitalize(self, instring):

        """ Capitalizes first character in string and lowers the rest.
        Ratemyprofessors.com is actually inanely case sensitive.
        """

        return instring[0].upper()+instring[1:].lower()

    def get_history(self):

        # Connect to mysql server
        con = mysql.connect(user=self.user, password=self.password)
        prof_list = con.cursor(buffered=True)

        # Table profs_list in profs DB is list of all professors at
        # UC with duplicates removed.
        prof_list.execute('USE profs')
        query = "SELECT last_name, first_name, campus FROM " + self.table
        #+ " WHERE campus='{}'".format(campus)

        prof_list.execute(query)
        print 'Using table {}'.format(self.table)


        # Now we have a [unique] list of all the professor names from all the campuses.
        # Which department are they in? Ratemyprofessors has that info, so save it if
        # there is a rmp page for prof.
        overall_rating = []
        dept = []
        names = []
        i, good_ct, bad_ct = 0, 0, 0
        for (last_name, first_name, campus) in prof_list:
            bad_tags = ['**','--']
            cont = False
            for tag in bad_tags:
                if tag in first_name or tag in last_name:
                    cont=True
            if cont:
                continue # Skip entries with no data. There are a few of these in the table.

            # If the middle name is more than an initial, remove it.
            mid = first_name.strip().split(' ')
            if len(mid) > 1:
                first_name = mid[0]# + mid[1][0]+'.'
            name = self.capitalize(first_name.strip()) +' ' + self.capitalize(last_name.strip())

            #name = 'Manoj Kaplinghat'

            rmp_search = 'https://www.ratemyprofessors.com/search.jsp?query='+name.replace(' ','+')
            br = mechanize.Browser()
            br.set_handle_robots(False) # ignore robots
            br.open(rmp_search)
            mylinks=[]
            for link in br.links():
                if 'ShowRatings' in str(link):
                    mylinks.append(link)
                    #br.follow_link(link)
                    # print link

            if len(mylinks) < 3:
                # There is no rating for given prof in this case.
                if self.verbose:
                    print "There doesn't appear to be a rmp page for {}".format(name)
                    print 'Skipping this prof.'
                overall_rating.append('0.0')
                dept.append('---')
                bad_ct += 1
            else:
                # There is a rating for given prof in this case.
                # rmp page I want is third link that contains 'ShowRatings'.
                br.follow_link(mylinks[2])
                raw = br.response().read()
                soup = BeautifulSoup(raw)
                tree = html.fromstring(raw)

                # Overall Rating. Need to scrape the rest of the ratings with dates!
                rmp_rating = tree.xpath('//div[@class="grade"]/text()')[0]
                overall_rating.append(rmp_rating)

                # Department the prof is in.
                rmp_dept = tree.xpath('//div[@class="result-title"]/text()')[0].lower()
                rmp_dept.replace('\r\n','')
                # ^This^ output is always "Professor in the biological sciences department", or similar.
                the_dept = rmp_dept[rmp_dept.find('the')+3:rmp_dept.find('department')].lstrip().rstrip()
                dept.append(the_dept)
                good_ct += 1
                #if self.verbose:
                #    print 'Found ratings for prof: {}'.format(name)



            # If the overall rating on rmp is 0.0 then there are no ratings at all.
            # Otherwise look for the rating as a function of time.
            if overall_rating[i] != '0.0':
                if self.verbose:
                    print 'Now look for rating as a funciton of time...'

                # First the current site needs to be fully loaded. UGH.
                # try_again = True
                # session = requests.Session() ##
                # load_more_link = br.links().next().base_url + '#'
                # response = session.get(load_more_link)
                # page = BeautifulSoup(response.content)
                # print page
                # pdb.set_trace()
                # while try_again:
                #     for link in br.links():
                #         if 'More' in link.text:
                #             mylinks.append(link)
                #             try_again = True
                #             continue

                #             lct += 1
                #             raw = br.response().read()
                #             soup = BeautifulSoup(raw)
                #             tree = html.fromstring(raw)
                #             #print soup
                #             #print '===================================================='
                #             comments=tree.xpath('//p[@class="commentsParagraph"]/text()')
                #             print len(comments)
                #             pdb.set_trace()
                #             br.follow_link(link)
                #             print 'Loading more ({})'.format(lct)
                #         else:
                #             try_again = False
                linknum = 1
                raw = br.response().read()
                soup = BeautifulSoup(raw)
                tree = html.fromstring(raw)
                #comments = tree.xpath('//p[@class="commentsParagraph"]/text()')
                #difficulty = tree.xpath('//span[@class="score inverse good"]/text()')

                # Scores have different labels ('average', 'poor' etc.), so need
                # to get rating with associated date with find_next().
                years_tot, ratings_tot = [], []
                dates = soup.find_all('div',class_='date')
                for date in dates:
                    ratings_tot.append(float(date.find_next(class_='score').text))
                    years_tot.append(str(date.text.strip()[-4::]))
 
                # For each year just take the average score. Although this
                # is throwing away data so it could be changed.
                years, ratings = [], []
                for year in np.unique(years_tot):
                    yr_ind = np.where(np.array(years_tot) == year)[0]
                    avg_rating = np.mean(np.array(ratings_tot)[yr_ind[0]])
                    ratings.append(avg_rating)
                    years.append(year)

                # Now we have ratings as a function of year. These, along with
                # department + prof name should be saved to a new SQL table!
                if self.verbose and i == 0:
                    print ("Generating new SQL table with ratings + department,"
                           "called profs_ratings_dept")

                # New table command.
                if i == 0:
                    # Open a new MySQL connection. 
                    con2 = mysql.connect(user=self.user, password=self.password)
                    sql_buff = con2.cursor(buffered=True)
                    sql_buff.execute('USE profs')

                    cmd = ('CREATE TABLE profs_ratings_dept (year INT, '
                           'campus VARCHAR(15), name VARCHAR(90), avg_rating FLOAT,'
                           'dept VARCHAR(50))')
                    try:
                        sql_buff.execute(cmd)
                    except:
                        print 'Dropping ratings DB.'
                        sql_buff.execute('DROP TABLE profs_ratings_dept;')
                        sql_buff.execute(cmd)

                # Insert data for each year into table. Each year = 1 row.
                for year, rating in zip(years, ratings):
                    data_cmd = ("""INSERT INTO profs_ratings_dept
                                 VALUES ({}, '{}', '{}', {}, '{}');""".format(year,
                                                              str(campus).lower().replace(' ','_'),
                                                              str(name),
                                                              rating,
                                                              the_dept))
                    try:
                        sql_buff.execute(data_cmd)
                        con2.commit()
                    except mysql.Error as err:
                        con2.rollback()
                        print 'There was an error with this command (i={}) {}:'.format(i, data_cmd)
                        print 'Error: {}'.format(err)

            i+=1
            print i

        sql_buff.close()
        prof_list.close()
        con.close()
        con2.close()
        return
