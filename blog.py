import webapp2
import cgi
import re
import logging
import json
from models import BlogPost
from google.appengine.ext import db
from google.appengine.api import memcache
from datetime import timedelta, datetime


blog_post_form="""
<form  method="post" action="/unit3/blog/newpost">
    <div>
    <label for="subject">Title: 
    <input id="subject"  name="subject" 
    value="%(title)s"/>
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
<h2><a href="/unit3/blog/%(id)s">%(title)s</a><h2>
</div>
<div>
%(post)s
</div>
</div>
<em>Posted on %(date)s</em>
"""


class BaseHandler(webapp2.RequestHandler):
    def write(self, template='', dictionary={'title':'','post':'','error':''}):
        self.response.out.write(template %  dictionary)
        
class Welcome(BaseHandler):
    def get(self):
        name = self.request.cookies.get("name")
        if name:
            self.response.out.write("Welcome, %s" % 
                    self.request.cookies.get("name"))
        else:
            self.redirect("/unit4/signup")    

class NewPost(BaseHandler):
    def get(self):
        self.write(blog_post_form)
    
    def post(self):
        title = self.request.get("title")
        post = self.request.get("post")
        if title and post: 
            newpost = BlogPost(title=title, post=post)
            key = newpost.put()
            self.redirect("/unit3/blog/%s"%key.id())
        else:
            self.write(blog_post_form, 
                    {'title':title, 'post':post, 
                        'error':"Both title and post are required."})

class Blog(BaseHandler):
    def get(self, post_id=None):
        if not post_id or post_id == None:
            posts = db.GqlQuery("SELECT * "
                    "FROM BlogPost ")
            self.write("<h1>Pearls Before Swine</h1>")
            for post in posts:
                
                self.write(post_listing, {"title":post.title, 
                    "post":post.post, "date":post.date_created,
                    "id":post.key().id()})
        else:
            key = db.Key.from_path("BlogPost", int(post_id))
            post = db.get(key)
            #posts = db.GqlQuery("SELECT * FROM BlogPost where ID = %s"%post_id)
            self.write("<h1>Pearls Before Swine</h1>")
            self.write(post_listing,  {"title":post.title, 
                "post":post.post, "date":post.date_created,
                "id":post.key().id()})


def get_front_page():
        posts_time = memcache.get("front_page")
        if posts_time:
            (posts, time) = posts_time
            return posts, (datetime.now() - time).seconds        
        logging.error("DB HIT")
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
    logging.error("DB HIT")
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
                
                self.write(post_listing, {"title":post.title, 
                    "post":post.post, "date":post.date_created.strftime("%A %d, %B %Y"),
                    "id":post.key().id()})
        else:
            post, age = get_individual_post(post_id)
            #posts = db.GqlQuery("SELECT * FROM BlogPost where ID = %s"%post_id)
            self.write(post_listing,  {"title":post.title, 
                "post":post.post, "date":post.date_created.strftime("%A %d, %B %Y"),
                "id":post.key().id()})
        self.write("<div> <em>Last DB Query %s seconds ago.</em></div>" % age)
        
class BlogJson(BaseHandler):
    def get(self, post_id=None):
        data_to_jsonify = []
        if not post_id or post_id == None:
            posts, age = get_front_page()
            for post in posts:
                data_to_jsonify.append({"subject":post.title, 
                    "content":post.post, "date":post.date_created.strftime("%A %d, %B %Y"),
                    "id":str(post.key().id())})
        else:
            post, age = get_individual_post(post_id)
            #posts = db.GqlQuery("SELECT * FROM BlogPost where ID = %s"%post_id)
            data_to_jsonify.append({"subject":post.title, 
                "content":post.post, "date":post.date_created.strftime("%A %d, %B %Y"),
                "id":str(post.key().id())})
        self.response.out.write(json.dumps(data_to_jsonify))
            
class Flush(BaseHandler):
    def get(self):
        self.write("Flushing")
        memcache.flush_all()