# Tenureism

Using a data base of all the professors employed at all the University of California campuses, this scrapes ratemyprofessors.com as a function of time for each professor; it also scrapes google scholar to get the number of first author and co-authorships for each professor per year.

Ratemyprofessors.com is understandably biased, but is neverthelsess a good overall indicator of performance, especially poor performance. Additionally, the number of papers a professor publishes isn't necessarily a good reflection of their research productivity, but if they haven't published in a peer-reviewed journal for many years, I think that can be considered a proverbial "red flag" for a future student looking for an active department and wanting to publish.

These data go back to 2004. Salaries are also included in this dataset.

With this larger data base, one can make predictions about how the department will more or less function in the coming academic year, in terms of publications and ostensible "lecture quality" from ratemyprofessors.

First generate the databases. This will download 7.5M from 'http://herschel.uci.edu/ketron/tenureism_data/' to $cwd/.data/ directory. MySQL needs to be installed. With user=root and password=password:
```
$ python make_sql_tables.py root password
```
