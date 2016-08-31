import requests
import lxml.html
import json
import re
import pdb
 
s = requests.Session()
 
r = s.get("http://www.ratemyprofessors.com/ShowRatings.jsp?tid=591412#")
e = lxml.html.fromstring(r.text)
pdb.set_trace()
csrf_token = e.xpath('//meta[@name="csrf-token"]/@content')[0]
newrelic_id = re.findall('xpid:"([^"]+)"', r.text)[0]
scripts = e.xpath("//script")
for script in scripts:
    if "max_id" in str(script.text):
        max_id  = int(re.findall("max_id: (\d+),", script.text)[0])
        item_id = int(re.findall("poll_id: (\d+),", script.text)[0])
pdb.set_trace()
s.headers = {'X-CSRF-Token': csrf_token,
             'X-NewRelic-ID': newrelic_id,
             'X-Requested-With':'XMLHttpRequest'}
r = s.get("http://stocktwits.com/streams/poll?stream=symbol&max={}&substream=top&item_id={}".format(max_id, item_id))
j = json.loads(r.text)
max_id = j['max']
r = s.get("http://stocktwits.com/streams/poll?stream=symbol&max={}&substream=top&item_id={}".format(max_id, item_id))
