import webapp2
import cgi
import logging
from google.appengine.ext import db
from models import User
from base import BaseHandler
import bcrypt

login_form = """
<form  method="post" action="/unit4/login">
    <div>
    <label for="username">LUsername: 
        <input id="username" name="username" />
     </div>
    <div>
    <label for="password">Password: 
    <input id="password" type="password" name="password"         
    </div>
    <div>
    %(error)s
    </div>
    <input type="submit" value="Submit">
    </form>
    <a href="/signup">Signup</a>
"""

class Logout(BaseHandler):
    def unset_cookie(self, cookie):
        self.response.headers.add_header('Set-Cookie', 
                str('%s=; Path=/' % cookie))
    def get(self):    
        self.unset_cookie("name")
        redirect = self.request.get("redirect")
        logging.error("redirect %s"%redirect)
        if redirect:
            self.redirect(redirect)
    
class Login(BaseHandler):
    def check_password(self, password, hashed):
        return bcrypt.hashpw(password, hashed) == hashed
    def set_cookie(self, username):
        self.response.headers.add_header('Set-Cookie', 
                str('name=%s; Path=/' % username))
    def get(self):    
        self.write(login_form)
    def post(self):
        user = db.Query(User)
        user.filter("user_name =", self.request.get("username"))        
        user.get()
        if user.count() and self.check_password(self.request.get("password"), 
                user[0].password):
            self.set_cookie(self.request.get("username"))
            redirect =  self.request.get("redirect")
            if redirect:
                self.redirect("redirect")
            self.redirect("/unit2/welcome")
        else:
            self.write(login_form, 
                    {'error':"Invalid login"})    
