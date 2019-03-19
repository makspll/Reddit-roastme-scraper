import requests
import time
import base64
import praw as pr
import json
url = 'https://www.reddit.com/r/RoastMe/'


#to get reddit's trust we need an access token from their api
handle = 'https://api.pushshift.io/reddit/search/submission/?'
#POST data included in the URL, kinda like an attachment
#we're asking for Client_credentials Flow for non-installed script type app

#username = 'l_IBFD5bZOT_IA'
#password = 'CYdIMyeTNQrzIQb1qXBdwM71rms'
#encoded = base64.b64encode(username+':'+password)

def getSubmissionsUrl(subreddit='RoastMe'):
    return handle + 'subreddit='+subreddit + '&fields=id'

def writeSubmissions(url,filename):
    r = requests.get(url).json()
    with open(filename+'.json','w') as f:
        json.dump(r,f)

print(getSubmissionsUrl())
writeSubmissions(getSubmissionsUrl(),'lol')
