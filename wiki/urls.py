import webapp2
import cgi
import re
from new_user import NewUser
from wiki import EditWikiPage, ViewWikiPage, WikiPageHistory
from copy import deepcopy
PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
    ('.*/_edit' + PAGE_RE, EditWikiPage),
    ('.*/_history' + PAGE_RE, WikiPageHistory),
    ('/wiki' + PAGE_RE, ViewWikiPage),
    ],
    debug=True)
