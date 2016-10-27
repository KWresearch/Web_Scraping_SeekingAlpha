"""
Author: TH
Date: 14/10/2016
Crawl an author's homepageInfo, followers, following and articles together with comments
"""
from getAuthorHomepageInfo import getAuthorHomepageInfoAndFollowersFollowing
from login import loginSA
from getAuthorArticles import getAuthorArticles
from getComments import getComments
url = "http://seekingalpha.com/author/mark-hibben/articles"
session = loginSA()[1]
#getAuthorHomepageInfoAndFollowersFollowing(session, url)
authorArticles = getAuthorArticles()
authorArticles.flag = False
authorArticles.getAuthorArticles(session, 'mark-hibben') 

