import webapp2
import cgi
import re
import logging
import json
import settings
from google.appengine.api import users
from models import BlogPost
from google.appengine.ext import db
from google.appengine.api import memcache
from datetime import timedelta, datetime

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
blog_post_form="""
<form  method="post" action="/blog/newpost">
    <div>
    <label for="subject">subject: 
    <input id="subject"  name="subject" 
    value="%(subject)s"/>
    </div>
    <div>
    <label for="content">Post: 
    <textarea cols="80" rows="20" id="content" name="content">%(post)s</textarea>    
    </div>
    <div class = "error">
    %(error)s
    </div>
    <input type="submit">
    </form>
"""
post_listing="""
<div>
<h2><a href="/blog/%(id)s">%(subject)s</a><h2>
</div>
<div>
%(post)s
</div>
</div>
<br/>
<em>Posted on %(date)s</em>
"""

edit_unauthorized_error ="""
<div>You are not authorized to edit this page.</div>
<div><a href="/login">Login</a>, <a href="/signup">signup</a>, or 
<a href="/login">return to homepage.</a></div>
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
        user = users.get_current_user()
        if not user:
            logging.info("Not a user!")
            self.write(html_header)
            self.write(edit_unauthorized_error)
            self.write(html_footer)
            return
        user.prefs =  db.GqlQuery(
              "SELECT * FROM UserPrefs WHERE user_id = :1",
              user.user_id()).get()
        if not user.prefs.can_edit:
            logging.info("user: %s can't edit." % user.nickname())
            self.write(html_header)
            self.write(edit_wiki_unauthorized_error)
            self.write(html_footer)            
            return
        self.write(html_header)
        self.write(blog_post_form)
        self.write(html_footer)
        
    
    def post(self):
        user = users.get_current_user()
        if not user:
            logging.info("Not a user!")
            self.write(html_header)
            self.write(edit_wiki_unauthorized_error)
            self.write(html_footer)            
            return
        user.prefs =  db.GqlQuery(
              "SELECT * FROM UserPrefs WHERE user_id = :1",
              user.user_id()).get()
        if not user.prefs.can_edit:
            logging.info("user: %s can't edit." % user.nickname())
            self.write(html_header)
            self.write(edit_wiki_unauthorized_error)
            self.write(html_footer)                   
            return

        subject = self.request.get("subject")
        content = self.request.get("content")
        if subject and content: 
            newpost = BlogPost(subject=subject, content=content)
            key = newpost.put()
            memcache.set("front_page", None)
            self.redirect("/blog/%s"%key.id())
        else:
            self.write(html_header)
            self.write(blog_post_form, 
                    {'subject':subject, 'content':content, 
                        'error':"Both subject and content are required."})
            self.write(html_footer)       

def get_front_page():
        posts_time = memcache.get("front_page")
        if posts_time:
            (posts, time) = posts_time
            return posts, (datetime.now() - time).seconds        
        logging.info("DB HIT (blog front page)")
        posts = db.GqlQuery("SELECT * "
                    "FROM BlogPost order by date_created desc")
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
        self.write(html_header)
        self.write("<h1>%s</h1>"%settings.BLOG_NAME)
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
        self.write(html_footer)
        
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
        
