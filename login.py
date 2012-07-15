import webapp2
import cgi
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
"""

class Logout(BaseHandler):
    def unset_cookie(self, cookie):
        self.response.headers.add_header('Set-Cookie', 
                str('%s=; Path=/' % cookie))
    def get(self):    
        self.unset_cookie("name")
        self.redirect("/unit4/signup")
    
class Login(BaseHandler):
    def check_password(self, password, hashed):
        return bcrypt.hashpw(password, hashed) == hashed
    def set_cookie(self, username):
        self.response.headers.add_header('Set-Cookie', 
                str('name=%s; Path=/' % username))
    def get(self):    
        self.write(login_form)
    def post(self):
        q = db.Query(User)
        q.filter("user_name =", self.request.get("username"))        
        q.get()
        if self.check_password(self.request.get("password"), q[0].password):
            self.set_cookie(self.request.get("username"))
            self.redirect("/unit2/welcome")
        else:
            self.write(login_form, 
                    {'error':"Invalid login"})    