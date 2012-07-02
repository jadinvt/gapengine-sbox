import webapp2
import cgi
import re
from copy import deepcopy

new_user_form="""
<form  method="post" action="/unit2/new_user">
    <div>
    <label for="username">Username: 
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

rot13_form="""
<form  method="post" action="/unit2/rot13">
    <input type="textarea" name ="text" value="%(value)s">
    <input type="submit">
    </form>
"""
form="""
<form  action="/testform">
    <input type="password" name ="q">
    <input type="submit">
    </form>
"""

class BaseHandler(webapp2.RequestHandler):
    form_dict={}

class MainPage(webapp2.RequestHandler):
    def get(self):
        #self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write(form)

class NewUser(BaseHandler):
    form_dict_blank={"username":'', "password":'', "verify":'',
            "email":'', "username_error":'', "password_error":'', 
            "verify_error": '', "email_error":''}
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
            self.redirect("/unit2/welcome?username=%s"%self.request.get("username"))

class Welcome(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Welcome, %s" % self.request.get("username"))

class TestHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        #q = self.request.get("q")
        self.response.out.write(self.request)

class Rot13(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(rot13_form % {'value':''})
    def post(self):
        text = self.request.get("text");
        rot13_text = ''
        for character in text:
            if 65 <= ord(character) <= 77:
                rot13_text += chr(ord(character) + 13)
            elif 97 <= ord(character) <= 109:
                rot13_text += chr(ord(character) + 13)
            elif 78 <= ord(character) <= 90:
                rot13_text += chr(ord(character) - 13)
            elif 110 <= ord(character) <= 122:
                rot13_text += chr(ord(character) - 13)
            else:
                rot13_text += character

        self.response.out.write(rot13_form % {"value":cgi.escape(rot13_text)})


app = webapp2.WSGIApplication([('/', MainPage),
    ('/testform', TestHandler),
    ('/unit2/new_user', NewUser),
    ('/unit2/welcome', Welcome),
    ('/unit2/rot13', Rot13)],
    debug=True)
