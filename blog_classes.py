import os
import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_BLOG_TITLE = 'default_blog'
DEFAULT_BLOG_POST_TITLE = 'New_Post'

# blog = Blog(parent=user.key(),author=user.key(),title=DEFAULT_BLOG_POST_TITLE)
class Blog(db.Model):
    author = db.UserProperty(required=True)
    title = db.StringProperty(required=True)
    def get_ten_posts():


    def get_all_posts():




def Blog_Key(title):
    return db.Key('Blog', title)


class Blogpost(db.Model):
    author = db.UserProperty(required=True)
    title = db.StringProperty(required=True)
    content = db.TextProperty()
    tags = db.StringListProperty()
    # results = db.GqlQuery("SELECT * FROM Blogpost WHERE tags = 'tech'")
    #blog_name = self.request.get('blog_name', DEFAULT_BLOG_TITLE)
    # blogpost = Blogpost(parent=blog_key(blog_name))
    date = db.DateTimeProperty(auto_now_add=True)


