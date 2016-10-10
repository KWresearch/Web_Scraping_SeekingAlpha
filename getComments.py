"""
Author: TH
Date: 09/10/2016
Crawl comments assosicated with an article
"""

import requests
from bs4 import BeautifulSoup as BS
from login import loginSA
import datetime
import json
import yaml
import getAuthorHomepageInfo as AHI
import pyodbc
class getComments:
    count = 0
    def getComments(self, session, url):
        # session is working while getting the full article, but it's not working while trying to
        # get data using a Ajax call. I added the cookie and it's working fine now. The cookie is a default value
        # which could be updated dynamicly (forth-coming).
        keys = yaml.load(open("keys.yaml",'r'))
        Cookie = keys['Cookie']
        userHeaders = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36", "Cookie": Cookie}
        
        r = session.get(url, headers = userHeaders)
        if r.text == '':
            return False
        total = json.loads(r.text)['total']
        comments = json.loads(r.text)['comments']
        user_likes = json.loads(r.text)['user_likes']
        #print(total, comments, userLikes)'
        #print(len(comments))
        #print(len(userLikes))
    
    
        for (commentID, comment) in comments.items():
            commentInfo = self.getCommentInfo(comment, user_likes)
            children = comment['children']
            self.count += 1
 
            #print("parent", self.count, commentInfo['id'], "likes:", commentInfo['user_likes'])
            #print(commentInfo)
            # insert author and then insert comment
            print(commentInfo["name_link"])
            authorInfo = AHI.getAuthorHomepageInfo(session, commentInfo["name_link"])       
            AHI.insertAuthorDB(authorInfo)
            self.insertCommentDB(commentInfo)
            print("parent", self.count, commentInfo['id'])
            self.getChildren(children)

            # please delete break
        return True
    def getChildren(self, comments):
        if len(comments) == 0:
            return
        for commentID, comment in comments.items():
            commentInfo = self.getCommentInfo(comment, None)
            children = comment['children']
            self.count += 1
            # position to add some code to insert DB
            authorInfo = AHI.getAuthorHomepageInfo(session, commentInfo["name_link"])
            AHI.insertAuthorDB(authorInfo)
            self.insertCommentDB(commentInfo)
            print("child", self.count, commentInfo['id'])
            getChildren(children)
    def insertCommentDB(self, comment):
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
            IF NOT EXISTS (SELECT * FROM dbo.SeekingAlpha_Comments \
            WHERE CommentID = ?) \
            BEGIN \
            INSERT dbo.SeekingAlpha_Comments (CommentID ,ArticleNumber ,NameLink ,DateTime ,Content ,UserID, UserIDCode, ParentID ,DiscussionID \
                , UserNick, UserMywebsiteUrl, CommenterUrl, AuthorSlug, ProfileAddToUrl, Level, BelongsToSaEditor, HtmlAnchor, Uri, AuthorsCommentFlag \
                ,IsPremiumAuthor, IsDeactivatedAuthor, Likes, UserLikes) \
            VALUES (?, ?, ?, ?, ?, ?,\
            ?, ?, ?, ?, ?, ?, \
            ?, ?, ?, ?, ?, ?, \
            ?, ?, ?, ?, ?) \
            END \
            ELSE \
            BEGIN \
            UPDATE dbo.SeekingAlpha_Comments SET UpdatedAt = ? WHERE CommentID = ? \
            END \
            END", comment['id'], comment['id'], comment['article_number'], comment['name_link'], comment['date_time'], comment['content'], comment['user_id'], comment['user_id_code'],comment['parent_id'], comment['discussion_id'], comment['user_nick'], comment['user_mywebsite_url'], comment['commenter_url'], comment['author_slug'], comment['profile_add_to_url'], comment['level'], comment['belongs_to_sa_editor'], comment['html_anchor'], comment['uri'], comment['authors_comment_flag'], comment['is_premium_author'], comment['is_deactivated_author'], comment['likes'], comment['user_likes'], now,  comment['id'])
            # unfinished business is just above. need to change the Insert update and 'article'
            conn.commit()
            return "success"
        except Exception as e:
            print(e," insertDB failed.")
            return "fail"
    def getCommentInfo(self, comment, userLikes):
        id = comment['id']
        content = comment['content']
        user_id= comment['user_id']
        user_id_code = comment['user_id_code']
        created_on = comment['created_on']
        parent_id = (None if comment['parent_id']=='null' else comment['parent_id'])
        discussion_id = comment['discussion_id'] 
        user_nick = comment['user_nick']
        user_mywebsite_url =  (None if comment['user_mywebsite_url']=='null' else comment['user_mywebsite_url'])
        commenter_url = comment['commenter_url']
        author_slug = (None if comment['author_slug']=='null' else comment['author_slug'])
        profile_add_to_url = comment['profile_add_to_url']
        level = comment['level']
        belongs_to_sa_editor = comment['belongs_to_sa_editor']
        html_anchor = comment['html_anchor']
        uri = comment['uri']
        authors_comment_flag = comment['authors_comment_flag']
        is_premium_author = comment['is_premium_author']
        is_deactivated_author = comment['is_deactivated_author']
        likes = comment['likes']
        # date time for the comment
        date_time = created_on.split('T')[0] + ' ' + created_on.split('T')[1].split('-')[0]
        # article id
        article_number = int(uri.split('/article/')[1].split("-")[0])
        user_likes = None
        #print(userLikes)
        baseUrl = "http://seekingalpha.com"
        if userLikes is not None:
            for user_like_key, use_like_value in userLikes.items():             
                if int(user_like_key) == id:
                    user_likes = use_like_value
                    break
        name_link = None
        if 'author' in commenter_url:
            name_link = baseUrl + commenter_url + "/articles"
        else:
            name_link = baseUrl + commenter_url + "/profile"
        return {
            "id": id,
            "content": content,
            "user_id": user_id,
            "user_id_code": user_id_code,
            "created_on": created_on,
            "parent_id": parent_id,
            "discussion_id": discussion_id,
            "user_nick": user_nick,
            "user_mywebsite_url": user_mywebsite_url,
            "commenter_url": commenter_url,
            "author_slug": author_slug,
            "profile_add_to_url": profile_add_to_url,
            "level": level,
            "belongs_to_sa_editor": belongs_to_sa_editor,
            "html_anchor": html_anchor,
            "uri": uri,
            "authors_comment_flag": authors_comment_flag,
            "is_premium_author": is_premium_author,
            "is_deactivated_author": is_deactivated_author,
            "likes": likes,
            "date_time": date_time,
            "article_number": article_number,
            "user_likes": user_likes,
            "name_link" : name_link
        }
    
if __name__ == "__main__":
    url1 = "http://seekingalpha.com/account/ajax_get_comments?id=4010696&type=Article"
    url2 = "http://seekingalpha.com/author/mark-hibben/ajax_load_regular_articles?author=true&userId=6965821&sort=recent"
    url3 = "http://seekingalpha.com/article/4010696-altria-showing-40-percent-mo-money"
    url4 = "http://seekingalpha.com/account/ajax_get_comments?id=4010696&type=Article"
    session = loginSA()[1]
    #print(loginSA()[0])
    temp = getComments()
    temp.getComments(session, url4)
    #print(temp.count)