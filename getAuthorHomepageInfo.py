"""
Author: TH
Date: 07/10/2016
Crawl an author's homepage and get all the metadata.
"""

import requests
from bs4 import BeautifulSoup as BS
from login import loginSA
import re
import yaml
import pyodbc
import datetime
from time import sleep
def getAuthorHomepageInfo(session, url):
    userHeaders = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}

    r = session.get(url, headers = userHeaders)
    soup = BS(r.content, 'html.parser')
    sleep(1)
    authorName = soup.find_all("div",{"class": "about-author-name"})[0].text
    authorImageUrl = soup.find_all("div", {"class": "about-author-image"})[0].img["src"]
    profileBioTruncate = soup.find_all("p", {"class": "profile-bio-truncate"})[0].text
    contributorSince = soup.find_all("div", {"class": "about-member-since"})[0].find_all("span")[1].text
    try:
        numArticles = soup.find_all("a", {"data-profile-tab-name", "articles"})[0].i.text
    except Exception as e:
        numArticles = 0
    try:
        numInstablogs = soup.find_all("a", {"data-profile-tab-name", "instablogs"})[0].i.text
    except Exception as e:
        numInstablogs = 0
        #print("{0} doesnot have instagrams".format(url))

    numComments = soup.find_all("a", {"data-profile-tab-name", "comments"})[0].i.text
    try:
        numStockTalks = soup.find_all("a", {"data-profile-tab-name", "stocktalks"})[0].i.text
    except Exception as e:
        numStockTalks = 0
    numFollowers = soup.find_all("a", {"data-profile-tab-name", "followers"})[0].i.text
    numFollowing = soup.find_all("a", {"data-profile-tab-name", "following"})[0].i.text

    if url.find('author') != -1:
        authorID = url[url.find('author')+7: url.find('/articles')]

    else:
        authorID = None

    if url.find('user') != -1:
        userID = url[url.find('user')+5: url.find('/profile')]
    else:
        userID = None

    #print(baseUrl)

    return {
        "authorName": authorName,
        "authorImageUrl": authorImageUrl,
        "profileBioTruncate" : profileBioTruncate,
        "contributorSince": contributorSince,
        "numArticles": numArticles,
        "numInstablogs": numInstablogs,
        "numComments": numComments,
        "numStockTalks": numStockTalks,
        "numFollowers": numFollowers,
        "numFollowing": numFollowing,
        "authorID": authorID,
        "userID": userID,
        "authorURL": url
    }

def getAuthorHomepageInfoAndFollowers(session, url):
    authorInfo = getAuthorHomepageInfo(session, url)
    insertAuthorDB(authorInfo)
    getFollowersList(session, url)
    getFollowingList(session, url)

def getFollowersList(session, url):
    baseUrl = None
    if url.find('author') != -1:
        baseUrl = url[0: url.find('/articles')]
    if url.find('user') != -1:
        baseUrl = url[0: url.find('/profile')]                  
    baseUrl1 = '/ajax_load_followers?page='
    baseUrl2 = '&author=true&userId=1400641&sort=recent'
    followers = []
    SAUrl = "http://seekingalpha.com"
    for page in range(0, 200):
        fullUrl = baseUrl + baseUrl1 + str(page) + baseUrl2
        #print(fullUrl)
        userHeaders = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}
        r = session.get(fullUrl, headers=userHeaders)
        soup = BS(r.content, 'html.parser')
        if len(soup.find_all("div")) == 0:
            break
        else:
            followersOnePage = soup.find_all("div", {"class": "media-body"})
            for oneFollower in followersOnePage:
                followerUrl = SAUrl + oneFollower.find_all("a")[0]["href"]
                authorInfo = getAuthorHomepageInfo(session, followerUrl)
                insertAuthorDB(authorInfo)
                #print(followerUrl)
                insertFollowerDB(url, followerUrl)
                #insertFollowerDB(url, followerUrl)
 
def getFollowingList(session, url):
    baseUrl = None
    if url.find('author') != -1:
        baseUrl = url[0: url.find('/articles')]
    if url.find('user') != -1:
        baseUrl = url[0: url.find('/profile')]                  
    baseUrl1 = '/ajax_load_following?page='
    baseUrl2 = '&author=false&userId=1400641&sort=recent'
    following = []
    SAUrl = "http://seekingalpha.com"
    for page in range(0, 200):
        fullUrl = baseUrl + baseUrl1 + str(page) + baseUrl2
        #print(fullUrl)
        userHeaders = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}
        r = session.get(fullUrl, headers=userHeaders)
        soup = BS(r.content, 'html.parser')
        if len(soup.find_all("div")) == 0:
            break
        else:
            followingOnePage = soup.find_all("div", {"class": "media-body"})
            for oneFollowing in followingOnePage:
                followingUrl = SAUrl + oneFollowing.find_all("a")[0]["href"]
                authorInfo = getAuthorHomepageInfo(session, followingUrl)
                insertAuthorDB(authorInfo)
                #print(followingUrl)
                insertFollowerDB(followingUrl, url)

                
def insertAuthorDB(authorInfo):
    keys = yaml.load(open("keys.yaml",'r'))
    server = keys['DBserver']
    user = keys['DBuser']
    password = keys['DBpassword']
    database = 'SeekingAlpha'
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+user+';PWD='+password)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    try:


        cursor.execute(" \
        BEGIN \
        IF NOT EXISTS (SELECT * FROM dbo.SeekingAlpha_Authors \
        WHERE NameLink = ?) \
        BEGIN \
        INSERT dbo.SeekingAlpha_Authors (NameLink, Name, ProfileBioTruncate, ContributorSince, NumArticles, NumInstablogs, \
        NumComments, NumStockTalks, NumFollowers, NumFollowing, AuthorID, UserID,  CreatedAt, UpdatedAt, AuthorImageUrl) \
        VALUES (?, ?, ?, ?, \
        ?, ?, ?, ?, ?, \
        ?, ?, ?, ?, ?, ?) \
        END \
        ELSE \
        BEGIN \
        UPDATE dbo.SeekingAlpha_Authors SET UpdatedAt = ? WHERE NameLink = ? \
        END \
        END", authorInfo['authorURL'], authorInfo['authorURL'],authorInfo['authorName'],authorInfo['profileBioTruncate'],authorInfo['contributorSince'], \
        authorInfo['numArticles'],authorInfo['numInstablogs'],authorInfo['numComments'],authorInfo['numStockTalks'],authorInfo['numFollowers'],authorInfo['numFollowing'], \
        authorInfo['authorID'],authorInfo['userID'], now, now, authorInfo['authorImageUrl'],now, authorInfo['authorURL'])
        # unfinished business is just above. need to change the Insert update and 'article'
        conn.commit()
        return "success"
    except Exception as e:
        print(e," insertDB failed.")
        return "fail"
def insertFollowerDB(author, follower):
    #print(author, follower)
    keys = yaml.load(open("keys.yaml",'r'))
    server = keys['DBserver']
    user = keys['DBuser']
    password = keys['DBpassword']
    database = 'SeekingAlpha'
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+user+';PWD='+password)
    cursor = conn.cursor()
    try:
        cursor.execute(" \
        BEGIN \
        IF NOT EXISTS (SELECT * FROM dbo.SeekingAlpha_Followers \
        WHERE AuthorLink = ? AND FollowerLink = ?) \
        BEGIN \
        INSERT dbo.SeekingAlpha_Followers (AuthorLink, FollowerLink) \
        VALUES (?, ?) \
        END \
        END", author, follower, author, follower)
        # unfinished business is just above. need to change the Insert update and 'article'
        conn.commit()
        return "success"
    except Exception as e:
        print(e," insertDB failed.")
        return "fail"
if __name__ == "__main__":
    url1 = "http://seekingalpha.com/author/rosenose/articles#regular_articles"
    url11 = "http://seekingalpha.com/author/max-greve/articles"
    url2 = "http://seekingalpha.com/user/741506/profile"
    url21 = "http://seekingalpha.com/user/5415171/profile"
    session = loginSA()[1]
    temp = getAuthorHomepageInfoAndFollowers(session, url21)
    #print(temp) 


