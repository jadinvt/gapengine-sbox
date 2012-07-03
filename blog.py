import webapp2
import cgi
import re
from copy import deepcopy
from models import BlogPost
from google.appengine.ext import db

blog_post_form="""
<form  method="post" action="/unit3/blog/newpost">
    <div>
    <label for="title">Title: 
    <input id="title"  name="title" 
    value="%(title)s"/>
    </div>
    <div>
    <label for="post">Post: 
    <input id="post" name="post" value="%(post)s"/>
    </div>
    <div class = "error">
    %(error)s
    </div>
    <input type="submit">
    </form>
"""
post_listing="""
<div>
%(title)s
</div>
<div>
%(post)s
</div>
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
            self.redirect("/unit3/blog/%s"%newpost.id)
        else:
            self.write(blog_post_form, 
                    {'title':title, 'post':post, 
                        'error':"Both title and post are required."})

class Blog(BaseHandler):
    def get(self, post_id=None):
        if not post_id or post_id == None:
            posts = db.GqlQuery("SELECT * "
                    "FROM BlogPost ")
            for post in posts:
                self.write("post_listing" % {"title":post.title, "post":post.post})
        else:
            self.write("List post %s <a href='./newpost'>Create Post</a>"%post_id)

