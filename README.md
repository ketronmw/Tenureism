# Tenureism

Compare the ratings of a single department across all the UC campuses. Using a data base of all the professors employed at all the University of California campuses, this scrapes ratemyprofessors.com as a function of time for each professor; it also scrapes google scholar to get the number of first author and co-authorships for each professor per year.

Ratemyprofessors.com is understandably biased, but is neverthelsess a good overall indicator of performance, especially poor performance. Additionally, the number of papers a professor publishes isn't necessarily a good reflection of their research productivity, but if they haven't published in a peer-reviewed journal for many years, I think that can be considered a kind of "red flag" for a future student looking for an active department and wanting to publish. 

These data go back to 2004. Salaries are also included in this dataset.

With this larger data base, one can make predictions about how the department will more or less function in the coming academic year, in terms of publications and ostensible "lecture quality" from ratemyprofessors.

The first step generates the databases. This will download 7.5M from 'http://herschel.uci.edu/ketron/tenureism_data/' to $cwd/.data/ directory. MySQL needs to be installed. The default login is user=root and password=password.

At the moment this only compares cumulative mean ratings between departments. Google is flagging get_publication_history.py as a bot. You can run this locally as 

```
>>> from tenureism import Tenureism
>>> chem = Tenureism('chemistry')
```
or on Heroku, at http://tenureism.herokuapp.com.
