from google.appengine.ext import db

class BlogPost(db.Model):
    """Models an individual post on our blog."""
    title = db.StringProperty(required=True)
    author = db.UserProperty()
    rating = db.RatingProperty()
    date_created = db.DateTimeProperty(auto_now_add=True)
    post = db.TextProperty(required=True)
