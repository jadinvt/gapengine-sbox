import webapp2
import cgi
import re
from new_user import NewUser
from blog import Blog, BlogJson, NewPost, Welcome, Flush
from copy import deepcopy
from login import Login, Logout

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
    ('.*/welcome/?', Welcome),
    ('/unit3/blog/(\d*)/?\.json', BlogJson),
    ('/unit3/blog/?\.json', BlogJson),    
    ('/unit3/blog/(\d*)', Blog),
    ('/unit3/blog', Blog),
     ('.*/login/?$', Login),
     ('.*/flush/?$', Flush),     
    ('/unit3/blog/newpost', NewPost),
    ('/unit2/rot13', Rot13),
    ('.*/logout/?', Logout),
    ('.*/signup/?', NewUser)],
    debug=True)
