import webapp2
import cgi
import re
import logging
import json
from models import BlogPost, WikiPage
from google.appengine.ext import db
from google.appengine.api import memcache
from datetime import timedelta, datetime

#logging.basicConfig(level=logging.INFO)
KEEP_HISTORY=True

logged_in_wiki_header_edit = """
<div>%(user_name)s | 
<a href='/logout?redirect=/wiki%(wiki_page_name)s'>logout</a>
"""

logged_in_wiki_header_view = """
<div>
<span><a href="/wiki/_edit%(wiki_page_name)s?version=%(version)s">edit</a>
|<a href="/wiki/_history%(wiki_page_name)s">history</a> 
</span>
<span>%(user_name)s  (<a href="/logout?redirect=/wiki%(wiki_page_name)s">
logout</a>)</span>
"""

logged_out_wiki_header = """
<div><a href=/login?redirect=%(wiki_page_name)s>login</a>
|<a href=/signup?redirect=%(wiki_page_name)s>Signup</a>
"""

edit_wiki_form="""
<form  method="post" action="/wiki/_edit%(wiki_page_name)s">
    <div>
    <h2>%(wiki_page_name)s</h2>
    </div>
    <div>
    <label for="content">Page Contents: 
    <input id="content" name="content" value="%(wiki_page_contents)s"/>
    <input id="subject" name="subject" type="hidden" value="%(wiki_page_name)s"/>
    </div>
    <div class = "error">
    %(error)s
    </div>
    <input type="submit">
    </form>
"""
blog_post_form="""
<form  method="post" action="/unit3/blog/newpost">
    <div>
    <label for="subject">subject: 
    <input id="subject"  name="subject" 
    value="%(subject)s"/>
    </div>
    <div>
    <label for="content">Post: 
    <input id="content" name="content" value="%(post)s"/>
    </div>
    <div class = "error">
    %(error)s
    </div>
    <input type="submit">
    </form>
"""
post_listing="""
<div>
<h2><a href="/unit3/blog/%(id)s">%(subject)s</a><h2>
</div>
<div>
%(post)s
</div>
</div>
<em>Posted on %(date)s</em>
"""

welcome="""
<div>Welcome, %(name)s!</div>
<div>Destinations
<ul>
<li><a href="/blog">Blog</a></li>
<li><a href="/wiki/">Wiki</a></li>
</ul>
</div>
"""

history_line="""
<div>%(version)s %(created)s %(content)s 
<a href="/wiki%(wiki_page_name)s?version=%(version)s">view</a>|
<a href="/wiki/_edit%(wiki_page_name)s?version=%(version)s">edit</a>
</div>
"""
class BaseHandler(webapp2.RequestHandler):
    def write(self, template='', dictionary={'subject':'','post':'','error':''}):
        self.response.out.write(template %  dictionary)
        
class Welcome(BaseHandler):
    def get(self):
        name = self.request.cookies.get("name")
        if name:
            self.write(welcome, {'name':name})
        else:
            self.redirect("/unit4/signup")    

class NewPost(BaseHandler):
    def get(self):
        self.write(blog_post_form)
    
    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        if subject and content: 
            newpost = BlogPost(subject=subject, content=content)
            key = newpost.put()
            memcache.set("front_page", None)
            self.redirect("/unit3/blog/%s"%key.id())
        else:
            self.write(blog_post_form, 
                    {'subject':subject, 'content':content, 
                        'error':"Both subject and content are required."})


def get_front_page():
        posts_time = memcache.get("front_page")
        if posts_time:
            (posts, time) = posts_time
            return posts, (datetime.now() - time).seconds        
        logging.info("DB HIT (blog front page)")
        posts = db.GqlQuery("SELECT * "
                    "FROM BlogPost ")
        posts = list(posts)
        time = datetime.now()
        memcache.set("front_page", (posts, time))
        return posts, 0

def get_individual_post(post_id):
    post_time = memcache.get("BlogPost"+post_id)
    if post_time:
        (post, time) = post_time
        return post, (datetime.now() - time).seconds
    logging.info("DB HIT (indiv post)")
    key = db.Key.from_path("BlogPost", int(post_id))
    post = db.get(key)
    time = datetime.now()
    memcache.set("BlogPost"+post_id, (post, time))
    return post, 0        

class Blog(BaseHandler):
    def get(self, post_id=None):
        self.write("<h1>Pearls Before Swine</h1>")
        if not post_id or post_id == None:
            posts, age = get_front_page()
            for post in posts:
                
                self.write(post_listing, {"subject":post.subject, 
                    "post":post.content, "date":post.date_created.strftime("%A %d, %B %Y"),
                    "id":post.key().id()})
        else:
            post, age = get_individual_post(post_id)
            #posts = db.GqlQuery("SELECT * FROM BlogPost where ID = %s"%post_id)
            self.write(post_listing,  {"subject":post.subject, 
                "post":post.content, "date":post.date_created.strftime("%A %d, %B %Y"),
                "id":post.key().id()})
        self.write("<div> <em>Queried %s seconds ago</em></div>" % age)
        
class BlogJson(BaseHandler):
    def get(self, post_id=None):
        data_to_jsonify = []
        if not post_id or post_id == None:
            posts, age = get_front_page()
            for post in posts:
                data_to_jsonify.append({"subject":post.subject, 
                    "content":post.content, "date":post.date_created.strftime("%A %d, %B %Y"),
                    "id":str(post.key().id())})
        else:
            post, age = get_individual_post(post_id)
            #posts = db.GqlQuery("SELECT * FROM BlogPost where ID = %s"%post_id)
            data_to_jsonify = {"subject":post.subject, 
                "content":post.content, 
                "date":post.date_created.strftime("%A %d, %B %Y"),
                "id":str(post.key().id())}
        self.response.headers.add_header('Content-Type' , 
                                         'application/json; charset=UTF-8')    
        self.response.out.write(json.dumps(data_to_jsonify))
        
def get_wiki_page(wiki_page_name, version=None):
    if not version:
        try:
            version = db.GqlQuery(
              "SELECT * FROM WikiPage WHERE subject = :1 ORDER BY version DESC",
              wiki_page_name).get().version
            logging.info("Version from db query %s" % version)
        except AttributeError: 
            version = 1
    wiki_page_time = memcache.get(wiki_page_name.join(str(version)))
    if wiki_page_time:
        logging.info("Page found in cache")
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
        version = self.request.get("version")
        logging.info("Getting page %s version %s" % (wiki_page_name, version))
        
        wiki_page, age, version = get_wiki_page(wiki_page_name, version)
        if wiki_page:
            user_name=self.request.cookies.get("name")
            logging.info("Viewing page as user: %s"%user_name)
            user_object = get_user_object(user_name)
            if user_name:
                logging.info("logged_in_wiki_header_view: %s"%wiki_page_name)
                self.write(logged_in_wiki_header_view, 
                        {'user_name':user_name, 
                    'wiki_page_name':wiki_page_name,
                    'version':version})
            else:
                self.write(logged_out_wiki_header, {'wiki_page_name':wiki_page_name})
                
            self.write("<h2>%s</h2>" % re.sub('/','',wiki_page.subject))
            self.write(wiki_page.content)
            self.write("<div> <em>Queried %s seconds ago</em></div>" % age)            
        else:
            self.redirect("/wiki/_edit%s" % wiki_page_name)            

class EditWikiPage(BaseHandler):
    
    def get(self, wiki_page_name):
        user_name=self.request.cookies.get("name")
        version=self.request.get("version")
        if user_name:
            user_object = get_user_object(user_name)
            logging.debug("logged_in_wiki_header_edit: %s"%wiki_page_name)
            self.write(logged_in_wiki_header_edit, 
                    {'user_name':user_name, 'wiki_page_name': wiki_page_name})
        else:
            self.redirect('/login')        

        wiki_page, age, version = get_wiki_page(wiki_page_name, version)
        if wiki_page:
            content = wiki_page.content
        else:
            content = ''
        
        self.write(edit_wiki_form, {'wiki_page_name':wiki_page_name, 
                                    'wiki_page_contents':content, 'error':""})
    
    def post(self, wiki_page_name):
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
        
        
        memcache.flush_all()
    
                
class Flush(BaseHandler):
    def get(self):
        self.write("Flushing")
        memcache.flush_all()
