import requests
import time
import base64
import praw as pr
import json
url = 'https://www.reddit.com/r/RoastMe/'


#to get reddit's trust we need an access token from their api
handle = 'https://api.pushshift.io/reddit/search/submission/?'
handleC = 'https://api.pushshift.io/reddit/comment/search/?'
handleComment = 'https://api.pushshift.io/reddit/submission/comment_ids/'
#POST data included in the URL, kinda like an attachment
#we're asking for Client_credentials Flow for non-installed script type app

#username = 'l_IBFD5bZOT_IA'
#password = 'CYdIMyeTNQrzIQb1qXBdwM71rms'
#encoded = base64.b64encode(username+':'+password)

def getSubmissionsUrl(subreddit='RoastMe'):
    return handle + 'subreddit='+subreddit + '&fields=id'

#subreddit name, epoch last time, sort True = descending score, false = ascending score
def getSubmissionIdsUrl(subreddit='roastme',before='1s',after='1d',sort=True):
    sortTxt = ''
    if sort:
        sortTxt = 'desc'
    else:
        sortTxt = 'asc'
    return handle +'&before='+before+'&after='+after+'&sort_type=score' +'&sort=desc'+'&limit=500'+'&subreddit='+subreddit + '&fields=url,id'
#'&after='+after+'&before=' +before

def requestAndWrite(url,filename):
    r = requests.get(url).json()
    with open(filename+'.json','w') as f:
        json.dump(r,f)
requestAndWrite(getSubmissionIdsUrl(),'lol')

def getCommentsByIdUrl(pid=''):
    return handleC +'&link_id='+pid + '&nest_level=1' + '&fields=body,score' + '&sort=score:asc' + '&limit = 500'
requestAndWrite(getCommentsByIdUrl('atsdhf'),'lol')
