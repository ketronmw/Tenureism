import os
import pdb
import re

import numpy as np
import pandas as pd
import mechanize
from bs4 import BeautifulSoup
import requests
from lxml import html
import mysql.connector as mysql

import db_info


class GetRatingHistory:


    def __init__(self, user='root', password='password', verbose=False, table='profs_list_unique'):
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
        # UC with duplicates removed. Select professors from only one campus.
        prof_list.execute('USE profs')
        query = "SELECT last_name, first_name FROM " + self.table #+ " WHERE campus='{}'".format(campus)
        prof_list.execute(query)
        print 'Using table {}'.format(self.table)


        # Now we have a [unique] list of all the professor names from all the campuses.
        # Which department are they in? Ratemyprofessors has that info, so save it if
        # there is a rmp page for prof.
        overall_rating = []
        dept = []
        names = []
        i, good_ct, bad_ct = 0, 0, 0
        for (last_name, first_name) in prof_list:
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

            if len(mylinks) < 3:  # There is no rating for given prof in this case.
                if self.verbose:
                    print "There doesn't appear to be a rmp page for {}".format(name)
                    print 'Skipping this prof.'
                overall_rating.append('0.0')
                dept.append('---')
                bad_ct += 1
            else:                 # There is a rating for given prof in this case.
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
            # Otherwise look for the rating as a function of year and average for each year.
            # Only save that average and the year. Maybe also the standard deviation.
            if overall_rating[i] != '0.0':
                print 'Now look for rating as a funciton of time.'
                pdb.set_trace()
                for link in br.links():
                    if 'ShowRatings' in str(link) and "text='Load More'" in str(link):
                        mylink = link

                # Keep loading the 'Load More' link until it's fully loaded.
                br.follow_link(mylink)
                while 'ShowRatings' in str(mylink) and "text='Load More'" in str(mylink):
                    br.follow_link(mylink)

                print 'this is wrong. I need a while loop enclosing whole thing.'
                pdb.set_trace()

            i+=1
#pdb.set_trace()
#dict = {'last_name':last_name, 'first_name'}

