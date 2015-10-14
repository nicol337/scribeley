import os
import cgi
import urllib
import re

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

ViewingPage = 0

def getBlogs(authorID, blog_name = None):
    if blog_name:
        return db.GqlQuery("SELECT * FROM Blog " +
            "WHERE authorID = :1 AND title = :2 " +
            "ORDER BY title" , authorID, blog_name)
    else:
        return db.GqlQuery("SELECT * FROM Blog " +
            "WHERE authorID = :1 " + 
            "ORDER BY title", authorID)

def getBlogPosts(authorID, blog_name, blog_post_name = None, tag_name = None):
    if blog_post_name:
        return db.GqlQuery("SELECT * FROM Blogpost " +
            "WHERE authorID = :1 AND blog = :2 AND title = :3 " +
            "ORDER BY date DESC", authorID, blog_name, blog_post_name)
    elif tag_name:
        return db.GqlQuery("SELECT * FROM Blogpost " +
            "WHERE authorID = :1 AND blog = :2 AND tags = :3 " +
            "ORDER BY date DESC", authorID, blog_name, tag_name)
    else:
        return db.GqlQuery("SELECT * FROM Blogpost " +
            "WHERE authorID = :1 AND blog = :2 " +
            "ORDER BY date DESC", authorID, blog_name)

def to_link(str):
    new_link='<a href="'+str+'">'+str+'</a>'
    if str.endswith(".jpg") or str.endswith(".png") or str.endswith(".gif"):
        new_link = str
    return jinja2.Markup(new_link)

class Blog(db.Model):
    authorID = db.StringProperty(required=True)
    authorNickname = db.StringProperty(required=True)
    title = db.StringProperty(required=True)

class Blogpost(db.Model):
    authorID = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    content = db.TextProperty()
    tags = db.StringListProperty()
    blog = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)

    def update(self, new_title, new_content, new_tags):
        self.title = new_title
        self.content = new_content
        self.tags = new_tags
        self.put()

class ErrorPage(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()

        if user:
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
    
        template = JINJA_ENVIRONMENT.get_template('404.html')
        self.response.write(template.render(template_values))

class HomePage(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()

        if user:
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

    def post(self):
        """Create a new blog for the logged-in user."""
        new_blog_name = self.request.get('blog_title')
        user = users.get_current_user()
        if new_blog_name:
            new_authorID = user.user_id()
            new_authorNickname = user.nickname()
            new_blog = Blog(authorID=new_authorID,authorNickname=new_authorNickname,title=new_blog_name)
            new_blog.put()
            self.redirect('/blog/'+new_authorID+'/'+new_blog_name+'/')
        else:
            self.redirect('/user/')

    def get(self):
        user = users.get_current_user()

        if user:
            template_url= 'user_home_page.html'
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

            blog_query= getBlogs(user.user_id())

            blogs = blog_query.run(limit=100)

            template_values = { 
                'user' : user,
                'url': url,
                'url_linktext': url_linktext,
                'blogs' : blogs
            } 

            template = JINJA_ENVIRONMENT.get_template(template_url)
            self.response.write(template.render(template_values))
        else:
            self.redirect('/')

class BlogHome(webapp2.RequestHandler):

    def post(self, authorID, blog_name, page_number):
        blogpost_title = self.request.get('blogpost_title')
        blogpost_content = self.request.get('blogpost_content')
        if blogpost_title and blogpost_content:

            blogpost_tags = self.request.get('blogpost_tags')
            tag_tokens = [tag.strip() for tag in blogpost_tags.split(',')]

            blogpost = Blogpost(authorID=authorID, title=blogpost_title, content=blogpost_content, blog=blog_name, tags=tag_tokens)
            blogpost.put()

            self.redirect('/blog/' + authorID + '/' + blog_name + '/')
        else:
            self.redirect('/blog/' + authorID + '/' + blog_name + '/')


    def get(self, authorID, blog_name, page_number=0):

        user = users.get_current_user()

        
        if page_number:
            ViewingPage = int(page_number)
        else:
            ViewingPage = 0

        if user:
            userID = user.user_id()
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            userID = ""
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        one_blog_query = getBlogs(authorID, blog_name)

        blogFound = False
        owner = False
        authorNickname = "error"
        for b in one_blog_query.run(limit=1):
            blogFound = True
            owner = (user and (user.user_id() == b.authorID))
            # owner = (str(user.user_id()) == str(b.authorID))
            authorNickname = b.authorNickname

        # if blogFound:
        blogpost_query = getBlogPosts(authorID, blog_name)

        number_of_posts_left = blogpost_query.count(offset=(ViewingPage+1)*10)

        moreposts = bool(number_of_posts_left)

        blogposts = blogpost_query.run(offset=ViewingPage*10,limit=10)

        blogpost_content = {}
        for post in blogpost_query.run(offset=ViewingPage*10,limit=10):
            blogpost_content[post.title]=post.content
            if len(post.content) > 500:
                blogpost_content[post.title]=post.content[:500]

        for key in blogpost_content.keys():
            text_tokens = blogpost_content[key].split(' ')
            for tok in text_tokens:
                if tok.startswith("http://") or tok.startswith("https://"):
                    blogpost_content[key]=blogpost_content[key].replace(tok,to_link(tok))

        blog_tags=[]
        for post in blogpost_query.run():
            for tag in post.tags:
                if tag not in blog_tags:
                    blog_tags.append(tag)
        blog_tags.sort()
            
        if user:
            blog_query = getBlogs(user.user_id())
            blogs = blog_query.run(limit=1000)    

        else:
            blogs = []

        template_values = { 
            'user' : user,
            'userID': userID,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'blogs' : blogs,
            'blogposts' : blogposts,
            'blog_name': blog_name,
            'authorID': authorID,
            'authorNickname': authorNickname,
            'blogpost_content' : blogpost_content,
            'blog_tags': blog_tags,
            'owner' : owner,
            'moreposts' : moreposts,
            'page_counter': ViewingPage
        } 
        template = JINJA_ENVIRONMENT.get_template("blog_home_page.html")
        self.response.write(template.render(template_values))

        # else:
        #     self.redirect('/error/')

class BlogpostPage(webapp2.RequestHandler):

    def isLink(self,tok):
        """Rudimentary url check"""
        tok = tok.lower()
        return (tok.startswith("http://") or tok.startswith("https://") 
            or tok.startswith("www") or tok.endswith(".edu") or tok.endswith(".com")
            or tok.endswith(".html") or tok.endswith(".jpg") or tok.endswith(".png")
            or tok.endswith(".gov") or tok.endswith(".org") or tok.endswith(".net")
            or tok.endswith(".int") or tok.endswith(".mil"))


    def post(self, authorID, blog_name, blogpost_name, mode):

        user = users.get_current_user()
        owner = False

        one_blog_query = getBlogs(authorID, blog_name)

        one_blog = one_blog_query.run(limit=1)
        
        for blog in one_blog:
            owner = (user and (user.user_id() == blog.authorID))

        edit = (mode == "edit" and owner == True)

        blogpost_query = getBlogPosts(authorID, blog_name, blogpost_name)

        blogpost = blogpost_query.run(limit=1)
        new_title = self.request.get('blogpost_title')
        new_content = self.request.get('blogpost_content')
        tag_str = self.request.get('blogpost_tags')
        new_tags = tag_str.split(',')

        if edit and owner:
            for post in blogpost:
                post.update(new_title, new_content, new_tags)

        self.redirect('/post/'+authorID+'/'+blog_name+'/'+new_title+"/view")

    def get(self, authorID, blog_name, blogpost_name, mode):

        user = users.get_current_user()
        owner = False

        if user:
            userID = user.user_id()
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            userID = ""
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        one_blog_query = getBlogs(authorID, blog_name)

        one_blog = one_blog_query.run(limit=1)
        authorNickname = "error"
        for blog in one_blog:
            owner = (user and (user.user_id() == blog.authorID))
            authorNickname = blog.authorNickname
                
        edit = (mode == "edit" and owner)

        blog_tags_query = getBlogPosts(authorID, blog_name)

        blogpost_query = getBlogPosts(authorID, blog_name, blogpost_name)

        blog_tags=[]
        for post in blog_tags_query.run(limit=1000):
            for tag in post.tags:
                if tag not in blog_tags:
                    blog_tags.append(tag)
        blog_tags.sort()

        for post in blogpost_query.run(limit=1):
            post.content.split(' ')
            text_tokens = post.content.split(' ')
            for tok in text_tokens:
                if self.isLink(tok):
                    post.content=post.content.replace(tok,to_link(tok))
            blogpost = post

        if user:
            blog_query = getBlogs(user.user_id())
            blogs = blog_query.run(limit=1000)   
        else:
            blogs = []

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'blogs' : blogs,
            'blogpost' : blogpost,
            'blog_name': blog_name,
            'authorID': authorID,
            'authorNickname': authorNickname,
            'one_blog': one_blog,
            'owner' : owner,
            'blog_tags' : blog_tags,
            'edit' : edit
        } 

        template = JINJA_ENVIRONMENT.get_template("blog_post_page.html")
        self.response.write(template.render(template_values))

class TagSearchPage(webapp2.RequestHandler):

    def get(self, authorID, blog_name, tag_name, page_number=0):

        if page_number:
            ViewingPage = int(page_number)
        else:
            ViewingPage = 0

        user = users.get_current_user()
        owner = False

        if user:
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        one_blog_query = getBlogs(authorID, blog_name)

        one_blog = one_blog_query.run(limit=1)
        authorNickname = "error"

        for blog in one_blog:
            owner = (user and (user.user_id() == blog.authorID))
            authorNickname = blog.authorNickname
        
        blogpost_query = getBlogPosts(authorID, blog_name, None, tag_name)

        number_of_posts_left = blogpost_query.count(offset=(ViewingPage+1)*10)

        moreposts = bool(number_of_posts_left)

        blogposts = blogpost_query.run(offset=ViewingPage*10,limit=10)

        blogpost_content = {}

        for post in blogpost_query.run(offset=ViewingPage*10,limit=10):
            blogpost_content[post.title]=post.content
            if len(post.content) > 500:
                blogpost_content[post.title]=post.content[:500]

        for key in blogpost_content.keys():
            text_tokens = blogpost_content[key].split(' ')
            for tok in text_tokens:
                if tok.startswith("http://") or tok.startswith("https://"):
                    blogpost_content[key]=blogpost_content[key].replace(tok,to_link(tok))

        blog_tags_query = getBlogPosts(authorID, blog_name) 

        blog_tags=[]

        for post in blog_tags_query.run(limit=1000):
            for tag in post.tags:
                if tag not in blog_tags:
                    blog_tags.append(tag)
        if user:
            blog_query = getBlogs(user.user_id())
            blogs = blog_query.run(limit=1000)   

        else:
            blogs = []

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'blogs' : blogs,
            'blogposts' : blogposts,
            'blogpost_content': blogpost_content,
            'blog_name': blog_name,
            'authorID': authorID,
            'authorNickname': authorNickname,
            'one_blog': one_blog,
            'tag_name' : tag_name,
            'blog_tags' : blog_tags,
            'owner' : owner,
            'moreposts': moreposts,
            'page_counter': ViewingPage
        } 

        template = JINJA_ENVIRONMENT.get_template("tag_search_page.html")
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', HomePage),
    (r'/user/', UserHome),
    (r'/blog/(.*)/(.*)/(.*)', BlogHome),
    (r'/post/(.*)/(.*)/(.*)/(.*)', BlogpostPage),
    (r'/search/(.*)/(.*)/(.*)/(.*)', TagSearchPage),
    ('/error/', ErrorPage)
], debug=True)
