import os
import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


MAIN_PAGE_FOOTER_TEMPLATE = """\
    <form action="/sign?%s" method="post">
      <div><textarea name="content" rows="3" cols="60"></textarea></div>
      <div><input type="submit" value="Sign Blog"></div>
    </form>

    <hr>

    <form>Blog name:
      <input value="%s" name="blog_name">
      <input type="submit" value="switch">
    </form>

    <a href="%s">%s</a>

  </body>
</html>
"""

DEFAULT_BLOG_NAME = 'default_blog'


# We set a parent key on the 'Blogposts' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def blog_key(blog_name=DEFAULT_BLOG_NAME):
    """Constructs a Datastore key for a Blog entity with blog_name."""
    return ndb.Key('Blog', blog_name)



class Blogpost(ndb.Model):
    """Models an individual Blog entry with author, content, and date."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)



class MainPage(webapp2.RequestHandler):

    def get(self):
        blog_name = self.request.get('blog_name',
                                          DEFAULT_BLOG_NAME)
        blogposts_query = Blogpost.query(
            ancestor=blog_key(blog_name)).order(-Blogpost.date)
        blogposts = blogposts_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'blogposts': blogposts,
            'blog_name': urllib.quote_plus(blog_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class Blog(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Blogpost' to ensure each Blogpost
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        blog_name = self.request.get('blog_name',
                                          DEFAULT_BLOG_NAME)
        blogpost = Blogpost(parent=blog_key(blog_name))

        if users.get_current_user():
            blogpost.author = users.get_current_user()

        blogpost.content = self.request.get('content')
        blogpost.put()

        query_params = {'blog_name': blog_name}
        self.redirect('/?' + urllib.urlencode(query_params))



application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Blog),
], debug=True)

