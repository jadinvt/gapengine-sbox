from google.appengine.ext import db

class BlogPost(db.Model):
    """Models an individual post on our blog."""
    title = db.StringProperty(required=True)
    post = db.TextProperty(required=True)
