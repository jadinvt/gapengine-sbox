import re
import settings
from google.appengine.ext import db
from google.appengine.api import memcache
from datetime import timedelta, datetime
import webapp2
import cgi
import json
import logging
from google.appengine.api import users
from models import User, UserPrefs
from base import BaseHandler
import bcrypt
login_page="""
<html>

<head>
<title>Example Step2 Authentication and Authorization</title>

<script type="text/javascript" src="/static/jquery-1.7.2.min.js"></script>

<script type="text/javascript">
 
 
  // submitting the form in this state will cause OpenID discovery to be
  // performed. The other possible state ("password") means that submitting
  // the form actually is supposed to transmit a username/password to the
  // server.
  var state = "discovery";
  // renders the login form un-clickable. Also shows a "spinner" to indicate
  // that we're waiting for the server
  function disableLoginForm() {
      $("#openid").attr("disabled", "disabled");
      $("#submit > input").attr("disabled", "disabled");
      
  }
  
  // makes it so that the login form is usable again. Hides the spinner.
  function enableLoginForm() {
      $("#openid").removeAttr("disabled");
      $("#submit > input").removeAttr("disabled");
      $("#spinner").css("display", "none");
  }

  // Sets up the login form for password login, i.e., it shows the password
  // field (which is hidden in the "discovery" state). In particular, we
  // need to do the following:
  // - bring the password field into visible view
  // - set up tab order such that tab flow is natural (user name->password->
  //   submit button)
  // - renames the submit button to ("sign in")
  function setupPasswordLogin() {
    state = "password";
    enableLoginForm();
    $("#password-div").css("position", "relative")
    $("#password-div").css("top", "-0px")
    $("#password").removeAttr("tabindex");
    $("#password")[0].focus();
    $("#submit-button").attr("value", "Sign in");
  }
  
   // Sets up the login form for "discovery" mode. This is the initial state, in
  // which the user simply types in an email address, and upon hitting enter
  // (or pressing the submit button), we try to perform discovery on the domain
  // in the email address.
  // In this state, the password field is hidden. However, to enable browsers to
  // auto-fill the username and password, the password field actually has to be
  // at the expected place in the DOM. So we're simply moving it out of the way.
  // In particular, we need to do the following:
  // - move the password field out of the page without actually "hiding" it or
  //   removing it from the DOM (which would mess with browsers' auto-fill
  //   mechanism)
  // - remove the password field from the tab order, so that tabbing in the
  //   username field brings you right to the submit button
  // - set the label of the submit button to "Continue"
  function setupDiscoveredLogin() {
    state = "discovery";
    enableLoginForm();
    $("#password").attr("tabindex", "9999");
    $("#password-div").css("position", "absolute")
    $("#password-div").css("top", "-5000px")
    $("#openid")[0].focus();
    $("#submit-button").attr("value", "Continue");
  }
  
  // Gets called when the user submits the form in "discovery" mode. In that
  // mode, we don't actually submit the form (the caller of this function
  // cancels the default submit behavior). Instead, we send an AJAX request
  // to the server, which will attempt to perform OpenID discovery on the
  // domain of the entered email address.
  function startDiscovery() {
    disableLoginForm();
    
    
    $.post("/login", {
        // the email address entered by the user
        openid: $("#openid").val(),
        
        // Other options checked on the page will be transmitted as
        // POST-body parameters. We format the request so that it looks just
        // like a regular submission of the form, with the POST-body parameter
        // "stage" set to the value "discovery".
       
        stage: "discovery"
    },

    // the function that will be called on return from the AJAX request.
    function(data) {
      if (data.status === "error") {
        // Discovery didn't work. Setup a normal login form with a
        // password field.
        setupPasswordLogin();

      } else if (data.status === "success") {
        // Discovery worked. data.redirectUrl has the Url of the OpenID OP with
        // a full OpenID request.
        document.location = data.redirectUrl;

      } else {
        alert("got weird response from server");
        enableLoginForm();
      }
    }, "json");
  }
 // called on page load
  $(document).ready(function() {
    // first, register a submit handler for the login form
    $("form").submit(function(e) {
      if (state === "discovery") {
          e.preventDefault();
          startDiscovery();
      }
       }
       )
        

    // then, setup the login form for the "discovery" state (i.e., hide
    // password field, etc).
    setupDiscoveredLogin();
  });
</script>
</head>
<body>

<h1>Login</h1>

<form id="form" method="post" action="/login">
<div id="loginform">
  <div id="preamble">
  Sign in with your<br/>
  <b>Email Address:</b>
  </div>
  <div id="email-div">
    <label for="openid">Email: </label>
    <input type="text" id="openid" name="openid" size="20" />
  </div>
  <div id="password-div">
    <label for="password">Password: </label>
    <input type="password" id="password" name="password" size="20" />
  </div>
  <div id="submit">
    <input id="submit-button" type="submit" value="Continue"/>
   
  </div>
  <div style="clear:both;"></div>
</div>
</form>
</body>
</html>
"""
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

providers = {
    'Google'   : 'gmail.com', # shorter alternative: "Gmail.com"
    'Yahoo'    : 'yahoo.com',
    'MySpace'  : 'myspace.com',
    'AOL'      : 'aol.com',
    'MyOpenID' : 'myopenid.com'
    # add more here
}


class Logout(BaseHandler):
    def unset_cookie(self, cookie):
        self.response.headers.add_header('Set-Cookie', 
                str('%s=; Path=/' % cookie))
    def get(self):    
        self.unset_cookie("name")
        
        user = users.get_current_user()
        logging.info("Logging out!  User: %s"%user.nickname())
        if user:
            logout_url = users.create_logout_url(self.request.uri)
            logging.info("Logging out!  User: %s"%logout_url)
            self.redirect(logout_url)
        
        redirect = self.request.get("redirect")
        logging.info("redirect %s"%redirect)
        if redirect:
            self.redirect(redirect)
        else:
            self.redirect('/')    

class Login(BaseHandler):
    def get(self):
        user = users.get_current_user()
        if user:  # signed in already         
            user.prefs = db.GqlQuery(
              "SELECT * FROM UserPrefs WHERE user_id = :1",
              user.user_id()).get()
            if not user.prefs:
                user.prefs = UserPrefs(user_id=user.user_id())
            user.prefs.put()    
            self.response.out.write("""
            Hello <em>%s</em>! [<a href="%s">sign out</a>] <br/>
            <a href="/blog"> Go to the blog</a>
            <a href="/wiki/"> Go to the wiki</a>
            """% (
                user.nickname(), users.create_logout_url(self.request.uri)))
            if user.prefs.can_edit:
                self.write("You can edit!")
            if user.prefs.is_admin:
                self.write("You're an admin!")
            
        else:     # let user choose authenticator
            self.write(login_page)
            #for name, uri in providers.items():
            #    self.response.out.write('[<a href="%s">%s</a>]' % (
            #        users.create_login_url(federated_identity=uri), name))
    def post(self):
        user = users.get_current_user()
        if user:  # signed in already            
            self.response.out.write('Hello <em>%s</em>! [<a href="%s">sign out</a>]' % (
                user.nickname(), users.create_logout_url(self.request.uri)))
        else:     # let user choose authenticator
            domain = self.request.POST.get('openid').split('@')[1]
            login_url = users.create_login_url('/login', federated_identity=domain)
            self.response.headers.add_header('Content-Type' , 
                                         'application/json; charset=UTF-8')
            if domain in providers.values():
                response_json = json.dumps({'status':'success', 'redirectUrl':login_url})                
            else:
                 response_json = json.dumps({'status':'error'})
            logging.info(response_json)     
            self.response.out.write(response_json)        
            #for name, uri in providers.items():
            #    self.response.out.write('[<a href="%s">%s</a>]' % (
            #        users.create_login_url(federated_identity=uri), name))
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


welcome="""
<div>Welcome, %(name)s!</div>
<div>Destinations
<ul>
<li><a href="/blog">Blog</a></li>
<li><a href="/wiki/">Wiki</a></li>
</ul>
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


class Flush(BaseHandler):
    def get(self):
        self.write("Flushing")
        memcache.flush_all()
