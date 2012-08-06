import webapp2
import cgi
import re
from new_user import NewUser
from blog import Blog, BlogJson, NewPost
from copy import deepcopy
from utils import Login, Logout
PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([                                       
    ('.*/blog/(\d*)/?\.json', BlogJson),
    ('.*/blog/?\.json', BlogJson),    
    ('.*/blog/(\d*)', Blog),
    ('.*/blog', Blog),
    ('.*/newpost', NewPost),
    ],
    debug=True)
