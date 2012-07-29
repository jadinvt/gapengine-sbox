from google.appengine.ext import db

class BlogPost(db.Model):
    """Models an individual post on our blog."""
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    author = db.UserProperty()
    rating = db.RatingProperty()
    date_created = db.DateTimeProperty(auto_now_add=True)
    date_modified = db.DateTimeProperty(auto_now=True)
    

class WikiPage(db.Model):
    """Models an individual page on our wiki."""
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    version = db.IntegerProperty(required=True)
    author = db.UserProperty()
    rating = db.RatingProperty()
    date_created = db.DateTimeProperty(auto_now_add=True)
    date_modified = db.DateTimeProperty(auto_now=True)
    

class User(db.Model):
    """Models a site user."""
    user_name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()
    user_id = db.IntegerProperty(required=True)
    
class UserPrefs(db.Model):    
    user_id = db.StringProperty(required=True)
    can_edit = db.BooleanProperty(default=False)
    is_admin = db.BooleanProperty(default=False)
