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

MAIN_PAGE_FOOTER_TEMPLATE = """\
    <form action="/sign?%s" method="post">
      <div><textarea name="content" rows="3" cols="200"></textarea></div>
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
    if user_name():
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
        user = users.get_current_user()

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': url,
            'url_linktext': url_linktext
        }   
    
        template = JINJA_ENVIRONMENT.get_template('home_page.html')
        self.response.write(template.render(template_values))


# class MainPage(webapp2.RequestHandler):

#     def get(self):
#         blog_name = self.request.get('blog_name',
#                                           DEFAULT_BLOG_NAME)
#         blogposts_query = Blogpost.query(
#             ancestor=blog_key(blog_name)).order(-Blogpost.date)
#         blogposts = blogposts_query.fetch(10)

#         if users.get_current_user():
#             url = users.create_logout_url(self.request.uri)
#             url_linktext = 'Logout'
#         else:
#             url = users.create_login_url(self.request.uri)
#             url_linktext = 'Login'

#         template_values = {
#             'blogposts': blogposts,
#             'blog_name': urllib.quote_plus(blog_name),
#             'url': url,
#             'url_linktext': url_linktext,
#         }

#         template = JINJA_ENVIRONMENT.get_template('blog_home.html')
#         self.response.write(template.render(template_values))

# class BlogPage(webapp2.RequestHandler):

    # def get(self, blog_name)
    
#     def post(self, ):
#         # We set the same parent key on the 'Blogpost' to ensure each Blogpost
#         # is in the same entity group. Queries across the single entity group
#         # will be consistent. However, the write rate to a single entity group
#         # should be limited to ~1/second.

#         # if user of this blog == users.get_current_user()

#         blog_name = self.request.get('blog_name',
#                                           DEFAULT_BLOG_NAME)

#         blogposts = Blogpost(parent=blog_key(blog_name))

#         if users.get_current_user():
#             blogpost.author = users.get_current_user()

#         blogpost.content = self.request.get('content')
#         blogpost.put()

#         query_params = {'blog_name': blog_name}
#         self.redirect('/?' + urllib.urlencode(query_params))

#         template_values = {
#             'blogposts': blogposts,
#             'blog_author' : 
#             'blog_name': urllib.quote_plus(blog_name),
#             'url': url,
#             'url_linktext': url_linktext,
#         }

#         # <form action="/sign?blog_name={{ blog_name }}" method="post">
#         #   <div><textarea name="content" rows="3" cols="60"></textarea></div>
#         #   <div><input type="submit" value="Sign Guestbook"></div>
#         #   </form>


#          template = JINJA_ENVIRONMENT.get_template('blog_home.html')
#          self.response.write(template.render(template_values))

class UserHome(webapp2.RequestHandler):

    def post(self, user_str):
        user = users.get_current_user()

        new_blog = Blog(author=user,title=self.request.get("blog_title"))
        new_blog.put()

        blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1 " +
                "ORDER BY title ASC", user)
        blogs = blog_query.run(limit=1000)

        if users.get_current_user():
            template_url= 'user_home_page.html'
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': url,
            'url_linktext': url_linktext,
            'user_str' : user_str,
            'blogs' : blogs
        } 
        template = JINJA_ENVIRONMENT.get_template(template_url)
        self.response.write(template.render(template_values))



    def get(self, user_str):
        user = users.get_current_user()

        if users.get_current_user():
            template_url= 'user_home_page.html'
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        # blog1 = Blog(author=user,title="title")
        # blog1.put()
        # blogs = db.Query(Blog)
        # blogs.filter("author = ", user)
        # blogs.fetch(limit=10)


        blog_query= db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1", user)
        blogs = blog_query.run(limit=1000)

        template_values = { 
            'user' : user,
            'url': url,
            'url_linktext': url_linktext,
            'user_str' : user_str,
            'blogs' : blogs
        } 
        template = JINJA_ENVIRONMENT.get_template(template_url)
        self.response.write(template.render(template_values))

class BlogHome(webapp2.RequestHandler):

    def post(self, user_str, blog_name):
        user = users.get_current_user()

        blog_title = blog_name

        blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1 ", user)
        blogs = blog_query.run(limit=1000)

        blogpost_query = db.GqlQuery("SELECT * FROM Blogpost " +
                "WHERE author = :1 ", user)
        blogposts = post_query.run(limit=10)

        if users.get_current_user():
            template_url= 'user_home_page.html'
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'url': url,
            'url_linktext': url_linktext,
            'user_str' : user_str,
            'blogs' : blogs,
            'blogposts' : posts
        } 
        template = JINJA_ENVIRONMENT.get_template(template_url)
        self.response.write(template.render(template_values))



    def get(self, user_str):
        user = users.get_current_user()

        if users.get_current_user():
            template_url= 'user_home_page.html'
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        blogpost = Blogpost(author=user, title="new blogpost", content="this is the new blogpost of today!")
        blogpost.put()
        # blog1 = Blog(author=user,title="title")
        # blog1.put()
        # blogs = db.Query(Blog)
        # blogs.filter("author = ", user)
        # blogs.fetch(limit=10)

        blog= db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1", user)
        blogs = blog_query.run(limit=1000)

        template_values = { 
            'user' : user,
            'url': url,
            'url_linktext': url_linktext,
            'user_str' : user_str,
            'blogs' : blogs
        } 
        template = JINJA_ENVIRONMENT.get_template(template_url)
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', HomePage),
    (r'/userhome/(.*)', UserHome)
    # ('/blog', BlogPage),
    # ('/sign', Blog),
], debug=True)
