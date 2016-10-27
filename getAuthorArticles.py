"""
Author: TH
Date: 01/10/2016
Crawl an author's homepage and get all the contributed URLs.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from login import loginSA
import json
from collectArticle import collectArticle
from insertDB import insertDB 
import yaml
from getComments import getComments
class getAuthorArticles:
    flag = False
    def getAuthorArtilesOnePage(self, session, url):
        keys = yaml.load(open("keys.yaml",'r'))
        Cookie = keys['Cookie']
        baseUrl = "http://seekingalpha.com"
        userHeaders = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}

        #print(url)

        r = session.get(url, headers=userHeaders)

        #print(r.text)

        print(json.loads(r.text)['page_count'])

        print(json.loads(r.text)['current_page'])
        if int(json.loads(r.text)['page_count']) < int(json.loads(r.text)['current_page']):
            print('We have collected all articles for this author.')
            self.flag = True
            return False
        else:
            htmlContent = json.loads(r.text)['html_content']
            htmlContent = BeautifulSoup(htmlContent, 'html.parser')
            #print(htmlContent)
            articles = htmlContent.find_all("div", {"class": "author-single-article"})
            for article in articles:
                link = article.find_all("div", {"class":"author-article-title"})[0]
                link = link.find_all("a")[0].get("href")
                fullUrl = urljoin(baseUrl, link)
                yield fullUrl
    def getAuthorArticles(self, session, authorName):
        baseUrlPart1 =  "http://seekingalpha.com/author/"
        baseUrlPart2 =  "/ajax_load_regular_articles?page="
        baseUrlPart3 = "&author=true&userId=173432&sort=recent"
        for page in range (0, 250):
            authorUrl = baseUrlPart1 + authorName + baseUrlPart2 + str(page) + baseUrlPart3
            articleUrls = self.getAuthorArtilesOnePage(session, authorUrl)
            print(articleUrls)
            
            if self.flag == True:
                print("{0} has {1} pages. All done.".format(authorName, page-1))
                break
            else:
                for articleUrl in articleUrls:
                    # get one article
                    try:
                        resDB = insertDB(session, articleUrl)
                        if resDB != "success":
                            print("Failed to insert article {0}, {1}, {2}".format(authorName, page, articleUrl))
                        else:
                            #pass
                            print("Successfully inserted article {0}, {1}, {2}".format(authorName, page, articleUrl))
                    except Exception as e:
                        print("insertDB error, ", e)
                    # get all the comments
                    articleNumber = articleUrl.split('article/')[1].split("-")[0]
                    urlComments = "http://seekingalpha.com/account/ajax_get_comments?id="+articleNumber+"&type=Article"
                    get_comments = getComments()
                    get_comments.getComments(session, urlComments)
if __name__ == "__main__":
    url1 = "http://seekingalpha.com/author/mark-hibben/ajax_load_regular_articles?author=true&userId=6965821&sort=recent"
    url2 = "http://seekingalpha.com/author/mark-hibben/ajax_load_regular_articles?page=15&author=true&userId=6965821&sort=recent"
    url3 = "http://seekingalpha.com/author/michael-fitzsimmons/ajax_load_regular_articles?page=1&author=true&userId=173432&sort=recent"

    session = loginSA()[1]
    #getAuthorArtilesOnePage(session, url1)
    getAuthorArticlesTEMP = getAuthorArticles()
    getAuthorArticlesTEMP.getAuthorArticles(session, 'mark-hibben')  