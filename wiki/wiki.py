
import re
import logging
from google.appengine.api import users
from models import BlogPost, WikiPage
from google.appengine.ext import db
from google.appengine.api import memcache
from datetime import timedelta, datetime
from base import BaseHandler
#logging.basicConfig(level=logging.INFO)
KEEP_HISTORY=True
html_header="""
<html>
<head>
<link rel="stylesheet" type="text/css" href="/static/base.css" />
</head>
<body>
<div id="content">
"""

html_footer="""
</div>
</body>
</html>
"""

edit_wiki_unauthorized_error ="""
<div>You are not authorized to edit this page.</div>
<div><a href="/login">Login</a>, <a href="/signup">signup</a>, or 
<a href="/login">return to homepage.</a></div>
"""
logged_in_wiki_header_edit = """
<div>%(user_name)s | 
<a href="%(logout_url)s">logout</a>
"""

logged_in_wiki_header_view = """
<div>
<span><a href="/wiki/_edit%(wiki_page_name)s?version=%(version)s">edit</a>
|<a href="/wiki/_history%(wiki_page_name)s">history</a> 
</span>
<span>%(user_name)s  <a href="%(logout_url)s">logout</a></span>
"""

logged_out_wiki_header = """
<div><a href=/login?redirect=%(wiki_page_name)s>login</a>
|<a href=/signup?redirect=%(wiki_page_name)s>signup</a>
"""

edit_wiki_form="""
<form  method="post" action="/wiki/_edit%(wiki_page_name)s">
    <div>
    <h2>%(wiki_page_name)s</h2>
    </div>
    <div>
    <label for="content">Page Contents: 
    <textarea cols="80" rows="20" id="content" name="content">%(wiki_page_contents)s</textarea>
    <input id="subject" name="subject" type="hidden" value="%(wiki_page_name)s"/>
    </div>
    <div class = "error">
    %(error)s
    </div>
    <input type="submit">
    </form>
"""
history_line="""
<div>%(version)s %(created)s %(content)s 
<a href="/wiki%(wiki_page_name)s?version=%(version)s">view</a>|
<a href="/wiki/_edit%(wiki_page_name)s?version=%(version)s">edit</a>
</div>
"""
def get_wiki_page(wiki_page_name, version=None):
    if not version:
        try:
            version = db.GqlQuery(
              "SELECT * FROM WikiPage WHERE subject = :1 ORDER BY version DESC",
              wiki_page_name).get().version
            logging.info("Version from db query %s" % version)
        except AttributeError: 
            version = 1
    logging.info("Looking for %s in mche"%wiki_page_name.join(str(version)))        
    wiki_page_time = memcache.get(wiki_page_name.join(str(version)))
    if wiki_page_time:
        logging.info("Page found in cache %s", wiki_page_name)
        (wiki_page, time) = wiki_page_time
        return wiki_page, (datetime.now() - time).seconds, version
    logging.info("DB HIT (wiki_page) %s %s" %  (wiki_page_name, version))
    db_str =  "Select * from WikiPage where subject = '%s' \
               and version = '%s'" % (wiki_page_name, version)
    logging.info("version type: %s" % type(version))
    result_set = db.GqlQuery("Select * from WikiPage where subject = :1 \
               and version = :2", wiki_page_name, long(version))

    result_set = list(result_set)
    logging.info("Got %s records for page %s version %s" % (str(len(result_set)),
                                                            wiki_page_name,
                                                            str(version)))
    try:
        wiki_page = result_set[0]
    except IndexError:
        return None, 0, 1
         
    time = datetime.now()
    memcache.set(wiki_page_name.join(str(version)), (wiki_page, time))
    return wiki_page, 0, version                

def get_user_object(user_name):        
    user_object = memcache.get(user_name)
    if user_object:        
        return user_object
    logging.info("DB HIT (user)")
    result_set = db.GqlQuery("Select * from User where user_name = '%s'" % user_name)    
    try:
        user = result_set[0]
    except IndexError:
        return None         
    
    memcache.set(user_name, user)
    return user_object

class ViewWikiPage(BaseHandler):
    def get(self, wiki_page_name=None):
        user = users.get_current_user()
        self.write(html_header)
        logging.info("ViewWikiPage %s", wiki_page_name)
        if user:
            user.prefs =  db.GqlQuery(
              "SELECT * FROM UserPrefs WHERE user_id = :1",
              user.user_id()).get()
        
        version = self.request.get("version")
        self.write(html_header)
        wiki_page, age, version = get_wiki_page(wiki_page_name, version)
        if wiki_page:
         #   user_object = get_user_object(user_name)
            if user and user.prefs.can_edit:
                self.write(logged_in_wiki_header_view, 
                        {'logout_url': users.create_logout_url(self.request.uri),
                         'user_name':user.nickname(), 
                    'wiki_page_name':wiki_page_name,
                    'version':version})
            else:
                self.write(logged_out_wiki_header, {'wiki_page_name':wiki_page_name})
                
            self.write("<h2>%s</h2>" % re.sub('/','',wiki_page.subject))
            self.write(wiki_page.content)
            self.write("<br/><br/><div> <em>Queried %s seconds ago</em></div>" % age)            
            self.write(html_footer)
        else:
            self.redirect("/wiki/_edit%s" % wiki_page_name)            

class EditWikiPage(BaseHandler):
    
    def get(self, wiki_page_name):
        user = users.get_current_user()
        self.write(html_header)
        if not user:
            logging.info("Not a user!")
            self.write(edit_wiki_unauthorized_error)
            self.write(html_footer)
            return
        user.prefs =  db.GqlQuery(
              "SELECT * FROM UserPrefs WHERE user_id = :1",
              user.user_id()).get()
        if not user.prefs.can_edit:
            logging.info("user: %s can't edit." % user.nickname())
            self.write(edit_wiki_unauthorized_error)
            self.write(html_footer)
            return

        # user.nickname()=self.request.cookies.get("name")
        version=self.request.get("version")
        # user_object = get_user_object(user_name)
        logging.debug("logged_in_wiki_header_edit: %s"%wiki_page_name)
        self.write(logged_in_wiki_header_edit, 
                {'logout_url': users.create_logout_url(self.request.uri),
                 'user_name':user.nickname(), 'wiki_page_name': wiki_page_name})            

        wiki_page, age, version = get_wiki_page(wiki_page_name, version)
        if wiki_page:
            content = wiki_page.content
        else:
            content = ''
        
        self.write(edit_wiki_form, {'wiki_page_name':wiki_page_name, 
                                    'wiki_page_contents':content, 'error':""})
        self.write(html_footer)
        
    def post(self, wiki_page_name):
        user = users.get_current_user()
        self.write(html_header)
        if not user:
            logging.info("Not a user!")
            self.write(edit_wiki_unauthorized_error)
            self.write(html_footer)
            return
        user.prefs =  db.GqlQuery(
              "SELECT * FROM UserPrefs WHERE user_id = :1",
              user.user_id()).get()
        if not user.prefs.can_edit:
            logging.info("user: %s can't edit." % user.nickname())
            self.write(edit_wiki_unauthorized_error)
            self.write(html_footer)
            return

        content = self.request.get("content")
        subject = self.request.get("subject")
        if not subject:
            subject = wiki_page_name
        wiki_page, age, version = get_wiki_page(wiki_page_name)

        if wiki_page:
            logging.info("modifying existing page")
            if KEEP_HISTORY:
                wiki_page =  WikiPage(subject=wiki_page.subject, 
                                      content=content,
                                      version=wiki_page.version + 1)
            else:                
                wiki_page.content = content
            
            wiki_page.put()
        else: 
            logging.info("adding new page")
            wiki_page = WikiPage(subject=subject, content=content, version=1)        
            key = wiki_page.put()            
        date_cached = datetime.now()
        memcache.set(subject, (wiki_page, date_cached))
        logging.info("redirecting %s" % wiki_page_name)
        self.redirect("/wiki%s" % wiki_page_name)

class WikiPageHistory(BaseHandler):
    def get(self, wiki_page_name):
        self.write(html_header)
        history = db.GqlQuery("Select * from WikiPage where subject = '%s'" 
                              % wiki_page_name)
        history = list(history)
        version_number = db.GqlQuery(
                "SELECT * FROM WikiPage ORDER BY version DESC").get().version
        self.write("<h2>%(subject)s History</h2>", {'subject':wiki_page_name})
        for version in history:
            self.write(history_line, 
                                    {'wiki_page_name':wiki_page_name,
                                     'version':version.version, 
                                     'content':version.content,
                                     'created':version.date_created})
        
        self.write(html_footer)
        memcache.flush_all()
    
                
class Flush(BaseHandler):
    def get(self):
        self.write("Flushing")
        memcache.flush_all()
