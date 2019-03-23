import requests
import time
import base64
import praw as pr
import json
import face_recognition
import numpy as np
import re
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

def jsonToDict(filename):
    with open (filename,'r') as f:
        datastore = json.load(f)
    return datastore

def requestToDict(url):
    r = requests.get(url).json()
    return r

def getCommentsBySubIdUrl(pid=''):
    print(handleC +'&q=*'+'&subreddit=roastme'+'&parent_id=t1_'+pid + '&fields=body,score,parent_id')
    return handleComment + pid

def getCommentByIdUrl(id):
    return handleC + '&ids=' + id + '&fields=body,score,id'

def getCommentsByIdsUrl(ids=[]):
    str = ''
    for a in ids:
            str +=  a + ','
    str = str[0:-1]
    return handleC + '&ids='+str + '&fields=body,score,id'

#given json list of comments from subreddit get top n comments by score
#have to have fields=[id]
def getTopComment(database):
    print(database)
    list = database["data"]
    maxId = ''
    maxScore = 0
    for comment in list:
        newMaxScore = max(maxScore,requestToDict(getCommentByIdUrl(comment["id"]))["data"][0]["score"])
        if newMaxScore != maxScore:
            maxId = comment["id"]
    return maxId

def loadSubmissions(limit,startDay=1,subreddit='roastme'):
    const_args = '&limit=500&fields=url,score,created_utc,id'
    baseurl = handle + '&subreddit='+ subreddit + const_args

    submissions_count = 0
    curr_startDay = startDay

    submissions = []
    print("loading Submissions")
    while submissions_count <= limit:
        before = str(curr_startDay) + 'd'
        after = str(curr_startDay+1) + 'd'
        data_dict = requestToDict(baseurl+'&after='+after+'&before='+before)
        capacity = limit - submissions_count
        submissions.extend(data_dict["data"][:capacity])
        submissions_count += len(data_dict["data"])
        print("current count: " + str(submissions_count))
    return submissions
#given a list of submission dictionaries update their score fields and remove ones
#without comments or below upvote threshold
def updateSubmissions(submissions,score_threshold,comments_threshold):
    filtered = submissions
    r = pr.Reddit(client_id='C-u-vJYPUPLdfg',
                  client_secret='Hyw3NkOJrL6qufVnIgt7EZ7Xj8k',
                  password='password123',
                  user_agent='testscript',
                  username='roastr123')
    print("authorised reddit, filtering and updating")
    deletable_indexes = []
    for index,sub_dict in enumerate(filtered):
        print("updating submission : " + str(index))
        id = sub_dict["id"]
        praw_submission = pr.models.Submission(r,id)
        print(str(praw_submission.score) + "," + str(praw_submission.num_comments))

        if (praw_submission.num_comments <= comments_threshold or praw_submission.score <= score_threshold \
        or (re.match('.(jpg|png)',praw_submission.url)) != None):
            deletable_indexes.append(index)
            print("deleted")
        else:
            submissions[index]["score"] = praw_submission.score
            submissions[index]["comments"] = loadTopComments(id,comments_threshold)

            picture = requests.get(praw_submission.url)
            file_name = praw_submission.url.split('/')[-1].split('.')[-1]
            print(praw_submission.url)
            with open('temp.'+file_name,'wb') as f:
                f.write(picture.content)
                submissions[index]["encodings"] = encodePicture('temp.'+file_name)

    removeIndexes(deletable_indexes,filtered)
def updateComments(comments,score_threshold):
    filtered = comments
    r = pr.Reddit(client_id='C-u-vJYPUPLdfg',
                  client_secret='Hyw3NkOJrL6qufVnIgt7EZ7Xj8k',
                  password='password123',
                  user_agent='testscript',
                  username='roastr123')
    print("authorised reddit, filtering and updating")
    deletable_indexes = []
    for index,com_dict in enumerate(filtered):
        print("updating comment : " + str(index))
        praw_submission = pr.models.Comment(r,com_dict["id"])
        print(str(praw_submission.score))
        if (praw_submission.score <= score_threshold):
            deletable_indexes.append(index)
            print("deleted")
        else:
            comments[index]["score"] = praw_submission.score
    removeIndexes(deletable_indexes,filtered)
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
    pic = face_recognition.api.load_image_file(filename)
    encodings = face_recognition.api.face_encodings(pic)
    faces = []
    for encoding in encodings:
        faces.append(np.array2string(encoding))
    return faces

#given a list of dictionaries of submissions merge comments and format for poem
def getAllComments(data):
    formated_comments = []
    for dict in data:
        comments = dict["comments"]
        for comment in comments:
            formated_comments.append(formatToPoem(comment))
    return formated_comments


def writeAllFormatedComments(datafile,filename):
    saveData(getAllComments(loadData(datafile)),filename)

def removeIndexes(indexes,array):
    for i in sorted(indexes,reverse=True):
        array.pop(i)

def formatComment(comment):
    return comment

def formatToPoem(comment):
    return comment

def saveData(dic,filename):
    with open(filename+'.json','w',encoding='utf-8') as f:
        json.dump(dic,f)

def loadData(filename):
    with open(filename+'.json','r',encoding='utf-8') as f:
        return json.load(f)

#all you need, right here, filenames are paths without extension
def createDatabase(data_filename,linguistic_filename,limit=10,upvote_threshold=50,comment_threshold=3,days_offset=1):
    raw_submissions = loadSubmissions(limit,days_offset)
    updateSubmissions(raw_submissions,upvote_threshold,comment_threshold)
    saveData(raw_submissions,data_filename)
    writeAllFormatedComments(data_filename,linguistic_filename)


createDatabase('test','allTest',10,40,5)
