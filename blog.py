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

def Blog_Key(title):
    return db.Key('Blog', title)

def User_Key(user):
    return db.Key('User', user)

def get_posts(blog_title, limit_count):
    results = Blogpost.all()
    results.ancestor(blog_key(blog_title))
    results.order("-date")
    if limit_count:
        results.fetch(limit_count)
    return results

def get_posts_with_tag(blog_title, tag, limit_count):
    results = Blogpost.all()
    results.ancestor(blog_key(blog_title))
    if tag:
        results.filter("tags =", tag)
    results.order("-date")
    if limit_count:
        results.fetch(limit_count)
    return results

def get_blogs(user_name, limit_count):
    results = Blog.all()
    results.ancestor(user_key(user_name))
    if limit_count:
        results.fetch(limit_count)
    return results


class Blogpost(db.Model):
    author = db.UserProperty(required=True)
    title = db.StringProperty(required=True)
    content = db.TextProperty()
    tags = db.StringListProperty()
    # results = db.GqlQuery("SELECT * FROM Blogpost WHERE tags = 'tech'")
    # get the current blog's name
    # blogpost = Blogpost(parent=blog_key(blog_name), author = self.request.get('current_user'), title=self.request.get('blog_title'))
    date = db.DateTimeProperty(auto_now_add=True)

class HomePage(webapp2.RequestHandler):

    def get(self):
        blog_name = self.request.get('blog_name',
        #                                   DEFAULT_BLOG_TITLE)
        # blogposts_query = Blogpost.query(
        #     ancestor=blog_key(blog_name)).order(-Blogpost.date)
        # blogposts = blogposts_query.fetch(10)

        # if users.get_current_user():
        #     url = users.create_logout_url(self.request.uri)
        #     url_linktext = 'Logout'
        # else:
        #     url = users.create_login_url(self.request.uri)
        #     url_linktext = 'Login'

        template_values = {
            'blogposts': blogposts,
            'blog_name': urllib.quote_plus(blog_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('blog_home.html')
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', HomePage),
    ('/sign', Blog),
], debug=True)
