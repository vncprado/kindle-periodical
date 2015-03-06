# coding:utf-8

"""
This is the main file that implements kindle periodical generation
All files are generated in temp folder
You need to put a kindlegen binary in bin folder in order to generate .mobi
"""

import os
import glob
import re
import random
import subprocess
from datetime import datetime
from time import strftime, localtime

from templates import *
from images import PeriodicalImages

DEBUG = True
BOOK_DIR_BASE = "temp/"


class Periodical:
    """
    Class that implements Kindle periodical file generation
    """
    
    def __init__(self, data, book_directory=BOOK_DIR_BASE,
                 user_id="test_id"):
        self.setMeta(data)
        self.user_id = user_id

        if not os.path.exists(book_directory):
            os.makedirs(book_directory)
        self.book_directory = book_directory

    def setMeta(self, data):
        self.title = data['title']
        self.creator = data['creator']
        self.publisher = data['publisher']
        self.subject = data['subject']
        self.description = data['description']
        self.filename = data['filename']

    def fixEncoding(self, input):
        """
        Correcting any wrong encoding
        """
        
        if isinstance(input, dict):
            return {self.fixEncoding(key):
                    self.fixEncoding(value) for key,
                    value in input.iteritems()}
        elif isinstance(input, list):
            return [self.fixEncoding(element) for element in input]
        elif isinstance(input, basestring):
            return input.encode('ascii', 'xmlcharrefreplace')
        else:
            return input

    def setupData(self, data):
        """
        Create/modify description, date, title and content from items
        in subscriptions
        """
        
        data = self.fixEncoding(data)
        for subscription in data:
            for item in subscription['items']:
                if item['published']:
                    if not "content" in item.keys():
                        item["content"] = u""

                    item["description"] = self.getDescription(item['content'])
                    item["date"] = datetime.fromtimestamp(
                        item['published']/1000).strftime('%d/%m/%Y')

                    if "title" in item.keys():
                        item['title'] = item['title'] + " - " + item["date"]
                    else:
                        item["title"] = item["description"][:15]\
                            + " - " + item["date"]
                    item["id"] = item["id"].replace(":","-")
                    item["id"] = item["id"].replace("_","")
        self.data = data
        
        self.removeEmptySubscriptions()

    def setContent(self, data):
        """
        Main function that creates all necessary files with provided data
        """

        self.setupData(data)
        if DEBUG:
            print "Setup Data OK"

        self.createArticles()
        if DEBUG:
            print "Articles OK"

        self.createContents()
        if DEBUG:
            print "Contents OK"

        self.createOPF()
        if DEBUG:
            print "OPF OK"

        self.createNCX()
        if DEBUG:
            print "NCX OK"

        created_file = self.createMOBI()
        if DEBUG and created_file:
            print "Book", created_file, "OK!"

        if DEBUG:
            print "Keeping temp files!"
        else:
            deleted = self.deleteTempFiles()
            if deleted:
                print "Temp Files Removed!"

        return created_file

    def createArticles(self):
        """
        Use templates/article.template file to format html article
        creating their files 
        """
        
        for subscription in self.data:
            for item in subscription['items']:
                filename = self.book_directory + item['id'] + '.html'
                if item['published']:
                    description = item["description"]
                    date = item["date"]
                    title = item["title"]

                # {$title} {$creator} {$description} {$title} {$content}
                html_data = ARTICLE_STR.format(title,
                                               subscription['title'],
                                               description,
                                               title,
                                               content,
                                               )

                self.writeFile(filename, html_data)

    def createContents(self):
        """
        Use templates/contents.template file to format content.html file
        """
        
        filename = self.book_directory + 'contents.html'
        sections = ""
        for subscription in self.data:
            sections = sections + '\t<h4>' + subscription['title'] + '</h4>\n'
            sections = sections + '\t<ul>\n'
            for item in subscription['items']:
                description = item["description"]
                date = item["date"]
                title = item["title"]
                sections = sections\
                    + '\t\t<li><a href="'\
                    + item['id']\
                    + '.html">'\
                    + title\
                    + '</a></li>\n'
            sections = sections + '\t</ul>\n'

        # {$sections}
        html_data = CONTENTS_STR.format(sections)

        self.writeFile(filename, html_data)

    def createOPF(self):
        """
        Use templates/content_opf.template to format content.opf file 
        """
        
        filename = self.book_directory + 'content.opf'

        manifest = ''
        items_ref = ''

        for subscriptions in self.data:
            for item in subscriptions['items']:
                manifest = manifest\
                    + '\t\t<item href="'\
                    + item['id']\
                    + '.html" media-type="application/xhtml+xml" id="item-'\
                    + item['id'] + '"/>\n'
                items_ref = items_ref\
                    + '\t\t<itemref idref="item-'\
                    + item['id']\
                    + '"/>\n'

        template_data = {'title': self.title,
                         'creator': self.creator,
                         'publisher': self.publisher,
                         'subject': self.subject,
                         'description': self.description,
                         'date': datetime.today().strftime('%Y-%m-%d'),
                         'items_manifest': manifest,
                         'items_ref': items_ref,
                         'identifier': random.choice(range(0, 10000))
                         }

        # {$identifier} {$title} {$creator} {$publisher} {$subject}
        # {$description} {$date} {$items_manifest} {$items_ref}
        html_data = CONTENTS_OPF_STR.format(template_data['identifier'],
                                            template_data['title'],
                                            template_data['creator'],
                                            template_data['publisher'],
                                            template_data['subject'],
                                            template_data['description'],
                                            template_data['date'],
                                            template_data['items_manifest'],
                                            template_data['items_ref'])

        self.writeFile(filename, html_data)

    def createNCX(self):
        """
        Use templates/nav-contents_ncx.template to format nav-contents.ncx
        """
        
        filename = self.book_directory + "nav-contents.ncx"
        sections = ''
        section_count = 0

        for subscription in self.data:
            
            if subscription['items']:
                section_first = subscription['items'][0]['id']
            else:
                break
            
            articles = ""
            for item in subscription['items']:
                # {$id} {$title} {$id} {$description} {$author}
                article = ARTICLE_NCX_STR.format(item['id'],
                                             item['title'],
                                             item['id'],
                                             self.
                                             getDescription(item['content']),
                                             self.creator)
                articles = articles + article + "\n"

            # {$section_id} {$section_title} {$section_first} {$articles}
            section = SECTION_NCX_STR.format("section-" + str(section_count),
                                         subscription['title'],
                                         section_first,
                                         articles)
            section_count = section_count + 1
            sections = sections + section

        # {$title} {$creator} {$sections}
        nc_content = NAV_CONTENTS_NCX_STR.format(self.title,
                                                 self.creator,
                                                 sections)
        
        self.writeFile(filename, nc_content)

    def createMOBI(self):
        """
        Uses (not given) bin/kindlegen to create mobi file
        """
        
        try:
            generate = os.path.dirname(os.path.realpath(__file__))\
                + '/bin/kindlegen -c2 '\
                + self.book_directory\
                + 'content.opf -o '\
                + self.filename + '.mobi'
            output = subprocess.call(generate, shell=True)
            if output > 1:
                raise Exception("Error creating .mobi file!")
            return self.filename + '.mobi'

        except Exception as e:
            print e
            return None

    def deleteTempFiles(self):
        """
        Remove temp files
        """
        
        try:
            filelist = []
            filelist = filelist + glob.glob(self.book_directory + "*.html")
            filelist = filelist + glob.glob(self.book_directory + "*.opf")
            filelist = filelist + glob.glob(self.book_directory + "*.ncx")

            print "Deleting"
            for f in filelist:
                os.remove(f)

            return True

        except:
            print "Error deleting temp files!"
            return False

    def writeFile(self, filename, content):
        """
        Write content to filename
        """
        
        file = open(filename, 'w+')
        file.write(content)

    def getDescription(self, description):
        """
        Description is a reduced version of content
        """
        
        description = self.stripTags(description)
        description = description.replace("\n", " ")
        description = description.replace("  ", " ")
        description = description.replace("        ", " ")
        description = description.replace(">", "")
        description = description.replace("<", "")
        description = description[:150]

        return description

    def stripTags(self, txt):
        """
        Just strip tags
        """
        
        return re.sub(r'<[^>]*?>', '', txt)

    def removeEmptySubscriptions(self):
        """
        Removes any subscription with no items
        """
        
        clean_data = []
        for subscription in self.data:
            if len(subscription['items']) == 0:
                continue
            clean_data.append(subscription)

        if len(clean_data) == 0:
            raise Exception("You don't have any unread feeds!")
        else:
            self.data = clean_data

if __name__ == "__main__":
    from test_content import content

    meta = {'title': "My Periodical " + datetime.today().strftime('%d/%m/%Y'),
            'creator': "Vinicius Prado",
            'publisher': "Vinicius Prado",
            'subject': "Periodical",
            'description': "Set of news articles in one .mobi file",
            'filename': "my_news_" + datetime.today().strftime('%Y-%m-%d'),
            }

    periodical = Periodical(meta)
    periodical.setContent(content)
