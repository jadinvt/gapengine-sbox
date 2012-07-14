import webapp2
import cgi
import re
from google.appengine.ext import db
from models import User
from copy import deepcopy
import bcrypt

new_user_form="""
<form  method="post" action="/unit2/new_user">
    <div>
    <label for="username">LUsername: 
        <input id="username" name="username" value="%(username)s"/>
        </label>%(username_error)s
    </div>
    <div>
    <label for="password">Password: 
    <input id="password" type="password" name="password" 
        value="%(password)s"/>%(password_error)s
    </div>
    <div>
    <label for="verify">Password (verify): 
    <input id="verify" type="password" name="verify" 
    value="%(verify)s"/>%(verify_error)s
    </div>
    <div>
    <label for="email">Email (optional): 
    <input id="email" name="email" value="%(email)s"/>
    %(email_error)s
    </div>

    <input type="submit">
    </form>
"""


class BaseHandler(webapp2.RequestHandler):
    form_dict={}

class NewUser(BaseHandler):
    form_dict_blank={"username":'', "password":'', "verify":'',
            "email":'', "username_error":'', "password_error":'', 
            "verify_error": '', "email_error":''}
    def create_user(self, user_dict):
        user = User(user_name=user_dict['username'], 
                password=bcrypt.hashpw(user_dict['password'],
                    bcrypt.gensalt()), email=user_dict['email'])
        user.put()

    def set_cookie(self, username):
        self.response.headers.add_header('Set-Cookie', 
                str('name=%s; Path=/' % username))
        

    def verify_username(self, username):
        user_regex = re.compile(r"^[1-zA-Z0-9_-]{3,20}$")
        return user_regex.match(username)
    def verify_password(self, password):
        pwd_regex = re.compile(r"^[1-zA-Z0-9_-]{3,20}$")
        return pwd_regex.match(password)
    def verify_email(self, email):
        if not email:
            return True
        email_regex = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
        return email_regex.match(email)
    def get(self):
        form_dict = deepcopy(self.form_dict_blank)
        self.response.out.write(new_user_form % form_dict)
    def post(self):
        form_error = False
        form_dict = deepcopy(self.form_dict_blank)
        form_dict["username"] = self.request.get("username")
        form_dict["email"] = self.request.get("email")
        if not self.verify_username(self.request.get("username")):
            form_dict["username_error"] = "Not a valid username."
            form_error = True
        if self.verify_password(self.request.get("password")):
            form_dict["password"] = self.request.get("password")
            if self.request.get("password") == self.request.get("verify"):
                form_dict["verify"] = self.request.get("verify")
            else:
                form_dict["verify_error"] = "Passwords do not match."
                form_error = True
                form_dict["password"] = form_dict["verify"] = ''
        else:
            form_dict["password_error"] = "Not a valid password."
            form_error = True
            form_dict["password"] = form_dict["verify"] = ''
            
        if self.verify_email(self.request.get("email")):
            form_dict["email"] = self.request.get("email")
        else:
            form_dict["email_error"] = "Not a valid email address."
            form_error = True
        if form_error:
            self.response.out.write(new_user_form % form_dict)
        else:
            self.create_user(form_dict)
            self.set_cookie(form_dict['username'])
            self.redirect("/unit2/welcome")
