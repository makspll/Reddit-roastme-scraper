import requests
import time
import base64
import praw as pr
import json
import face_recognition
import numpy as np
import re,sys,os
url = 'https://www.reddit.com/r/RoastMe/'


#to get reddit's trust we need an access token from their api
handle = 'https://api.pushshift.io/reddit/search/submission/?'
handleC = 'https://api.pushshift.io/reddit/search/comment/?'
handleComment = 'https://api.pushshift.io/reddit/submission/comment_ids/'
#POST data included in the URL, kinda like an attachment
#we're asking for Client_credentials Flow for non-installed script type app

#username = 'l_IBFD5bZOT_IA'
#password = 'CYdIMyeTNQrzIQb1qXBdwM71rms'
#encoded = base64.b64encode(username+':'+password)
# Print iterations progress
def progress(count, total, status=''):
    bar_len = 30
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

def requestAndWrite(url,filename):
    with open(filename+'.json','w') as f:
        r = requests.get(url).json()
        json.dump(r,f)

def jsonToDict(filename):
    with open (filename,'r') as f:
        datastore = json.load(f)
    return datastore

def requestToDict(url):
    r = requests.get(url).json()
    return r

#given json list of comments from subreddit get top n comments by score
#have to have fields=[id]

def loadSubmissions(table,startDay=1,subreddit='roastme'):
    const_args = '&limit=500&fields=url,title,score,created_utc,id&sort_type=num_comments&sort=desc'
    baseurl = handle + '&subreddit='+ subreddit + const_args

    submissions = table
    before = str(startDay) + 'd'
    after = str(startDay+1) + 'd'

    data_dict = requestToDict(baseurl+'&after='+after+'&before='+before)

    data = data_dict["data"]
    #print(data)
    if len(data) == 0:
        print("NO MORE DATA, could not get requested number, found: "+str(submissions_count))
        return -1
    submissions.extend(data)
        #print("current count: " + str(submissions_count))
    return startDay
#given a list of submission dictionaries update their score fields and remove ones
#without comments or below upvote threshold
def updateSubmissions(submissions,limit,score_threshold,comments_threshold):

    r = pr.Reddit(client_id='C-u-vJYPUPLdfg',
                  client_secret='Hyw3NkOJrL6qufVnIgt7EZ7Xj8k',
                  password='password123',
                  user_agent='testscript',
                  username='roastr123')

    new = []
    for index,sub_dict in enumerate(submissions):
        id = sub_dict["id"]
        praw_submission = pr.models.Submission(r,id)
        progress(len(new),limit,'encoding')
        if(len(new) >= limit):
            return new

        if not (praw_submission.num_comments <= comments_threshold or praw_submission.score <= score_threshold \
        or not (praw_submission.url.endswith(('.png','.jpg')))):
            copied_submission = submissions[index].copy()
            file_name = praw_submission.url.split('/')[-1].split('.')[-1]

            with open('temp.'+file_name,'wb') as f:
                picture = requests.get(praw_submission.url)

                f.write(picture.content)
                encodings = encodePicture('temp.'+file_name)
                if len(encodings) != 0:
                    copied_submission["score"] = praw_submission.score
                    copied_submission["comments"] = loadTopComments(id,comments_threshold)
                    copied_submission["encodings"] = encodings
                    new.append(copied_submission.copy())
    #removeIndexes(deletable_indexes,filtered)
    return new

def loadTopComments(id,limit):
    r = pr.Reddit(client_id='C-u-vJYPUPLdfg',
                  client_secret='Hyw3NkOJrL6qufVnIgt7EZ7Xj8k',
                  password='password123',
                  user_agent='testscript',
                  username='roastr123')
    praw_submission = pr.models.Submission(r,id)
    praw_submission.comment_sort = 'best'
    submission_comments = praw_submission.comments
    submission_comments.replace_more(limit=0)
    comments = []
    for index,top_level_comment in enumerate(submission_comments):
        comments.append(formatComment(top_level_comment.body))
        if (index+1) >= limit:
            break
    return comments

def encodePicture(filename):
    try:
        pic = face_recognition.api.load_image_file(filename)
    except:
        return []
    encodings = face_recognition.api.face_encodings(pic)
    faces = []
    for encoding in encodings:
        faces.append(np.array2string(encoding))
    return faces

#given a list of dictionaries of submissions merge comments and format for poem
def getAllComments(data):
    formated_comments = []
    for index,dict in enumerate(data):
        comments = dict["comments"]
        for comment in comments:
            formated_comments.append(formatToPoem(comment))
    return formated_comments

#----------------------------USEFUL PUBLIC STUFF ------------------------------#

#give it the datafile name of the database and will create linguistic database with filename

def writeAllFormatedComments(datafile,filename):
    saveData(getAllComments(loadData(datafile)),filename)

#this is just for general clean up
def formatComment(comment):
    return bytes(comment.strip(),'utf-8').decode('utf-8','ignore')




#fiona use this to format, if isn't as clean as you need, make changes here
def formatToPoem(comment):
    newlines = re.sub(r'\n',' ',comment.lower().strip('. '))
    punctuated = re.sub(r'[!?]','.',newlines)
    repetitions = re.sub(r'(([^A-Za-z])\2\2*)',r'\2',punctuated)
    characterReptitions = re.sub(r'((.)\2\2\2*)',r'\2',repetitions)
    result = re.sub('[^A-Za-z.\"\' ]','',characterReptitions)
    return result



#filepath without extension !
#will append existing data if same file exists
def saveData(data,filename):
    if not os.path.isfile(filename+'.json'):
        with open(filename+'.json','w') as f:
            json.dump(data,f)
    else:
        feeds = loadData(filename)

        feeds.extend(dic)
        with open(filename+'.json',mode = 'w') as f:
            f.write(json.dumps(feeds))
#will pull into list of dictionaries
def loadData(filename):
    with open(filename+'.json','r') as f:
        return json.load(f)


#the sub has around 236,000 submissions over 3 years
#takes in:
#filename for data, ling data
#amount of submissions to pull
#minimum upvotes (too high might end up with not many submissions)
#minimum comments (same as comments pulled)
#optional - days offset (integer how many days ago to start indexing)
#all you need, right here, filenames are paths without extension
def createDatabase(data_filename,linguistic_filename,limit=10,upvote_threshold=50,comment_threshold=3,days_offset=1):
    curr_startDay = days_offset
    submissions_count = 0

    while submissions_count < limit:
        progress(submissions_count,limit,'processing')
        submissions_batch = []
        capacity = limit - submissions_count

        loadSubmissions(submissions_batch,curr_startDay)
        submissions_batch = updateSubmissions(submissions_batch,capacity,upvote_threshold,comment_threshold)

        curr_startDay +=1

        batch_count = len(submissions_batch)

        saveData(submissions_batch[:capacity],data_filename)
        submissions_count += batch_count
        writeAllFormatedComments(data_filename,linguistic_filename)
