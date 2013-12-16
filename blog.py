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
    reference = db.ReferenceProperty(Blog, required=True)
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


class UserHome(webapp2.RequestHandler):

    def post(self, user_str):
        # user = users.get_current_user()
        new_blog_name = self.request.get('blog_title')
        new_blog = Blog(author=users.get_current_user(),title=new_blog_name)
        new_blog.put()

        query_params = {'user': user_str}
        self.redirect('/userhome/'+user_str)
        
        # self.redirect('/userhome/' + urllib.urlencode(query_params))

        # blog_query = db.GqlQuery("SELECT * FROM Blog " +
        #         "WHERE author = :1 " +
        #         "ORDER BY title ASC", user)
        # blogs = blog_query.run(limit=1000)

        # if users.get_current_user():
        #     template_url= 'user_home_page.html'
        #     url = users.create_logout_url(self.request.uri)
        #     url_linktext = 'Logout'
        # else:
        #     template_url = 'home_page.html'
        #     url = users.create_login_url(self.request.uri)
        #     url_linktext = 'Login'

        # template_values = { 
        #     'user' : user,
        #     'url': url,
        #     'url_linktext': url_linktext,
        #     'user_str' : user_str,
        #     'blogs' : blogs
        # } 
        # template = JINJA_ENVIRONMENT.get_template(template_url)
        # self.response.write(template.render(template_values))

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

    def post(self, blog_name):
        blog_post_title = self.request.get('blog_post_title')
        blog_post_content = self.request.get('blog_post_content')
        # blog_post_tags = self.request.get('blog_post_content')
        blog_post = Blogpost(author=users.get_current_user(),title=blog_post_title,content=blog_post_content)
        new_blog.put()

        query_params = {'new_blog_name': new_blog_name}
        self.redirect('/bloghome?' + urllib.urlencode(query_params))
        __
        # user = users.get_current_user()

        # current_blog_query = db.GqlQuery("SELECT * FROM Blog "+
        #         "WHERE title = :1 ", blog_name)
        # current_blog = current_blog_query.run(limit=1)

        # blogpost_query = db.GqlQuery("SELECT * FROM Blogpost " +
        #         "WHERE author = :1 AND ", user, current_blog)
        # blogposts = post_query.run(limit=10)

        # blog_query = db.GqlQuery("SELECT * FROM Blog " +
        #         "WHERE author = :1 ", user)
        # blogs = blog_query.run(limit=1000)

        # if users.get_current_user():
        #     url = users.create_logout_url(self.request.uri)
        #     url_linktext = 'Logout'
        # else:
        #     url = users.create_login_url(self.request.uri)
        #     url_linktext = 'Login'

        # template_values = { 
        #     'user' : user,
        #     'url': url,
        #     'url_linktext': url_linktext,
        #     'user_str' : user_str,
        #     'blogs' : blogs,
        #     'current_blog' : current_blog,
        #     'blogposts' : posts
        # } 
        # template = JINJA_ENVIRONMENT.get_template("blog_home_page.html")
        # self.response.write(template.render(template_values))



    def get(self, blog_name):
        user = users.get_current_user()

        if users.get_current_user():
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        blogpost = Blogpost(author=user, title="new blogpost", content="this is the new blogpost of today!")
        blogpost.put()

        blogpost_query = db.GqlQuery("SELECT * FROM Blogpost " +
                "WHERE author = :1 AND ", user, current_blog)
        blogposts = post_query.run(limit=10)

        blog_query = db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1 ", user)
        blogs = blog_query.run(limit=1000)    

        blog= db.GqlQuery("SELECT * FROM Blog " +
                "WHERE author = :1 AND title = :2", user, blog_name)

        blogs = blog_query.run(limit=1000)

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'user_str' : user_str,
            'blogs' : blogs,
            'blog' : blog,
            'blogposts' : posts
        } 
        template = JINJA_ENVIRONMENT.get_template("blog_home_page.html")
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', HomePage),
    (r'/userhome/(.*)', UserHome),
    (r'/bloghome/(.*)', BlogHome)
    # ('/sign', Blog),
], debug=True)
