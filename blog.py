import webapp2
import cgi
import re
from models import BlogPost
from google.appengine.ext import db

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


