import webapp2
import cgi
import re
from new_user import NewUser
from utils import Flush, Login, Logout, Welcome
from copy import deepcopy
PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([                                       
     ('.*/login/?$', Login),
     ('.*/flush/?$', Flush),     
    ('.*/logout/?', Logout),
    ('.*/signup/?', NewUser),
    ('.*', Welcome),
    ],
    debug=True)
