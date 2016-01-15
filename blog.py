# ??? add redirect to username page if a user signs in on any page and doesn't have a username picked yet.
# lsof -i :<port number> then kill with pid
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

def getBlogsQuery(authorname, blog_name = None):
    if blog_name:
        return db.GqlQuery("SELECT * FROM Blog " +
            "WHERE authorname = :1 AND title = :2 " +
            "ORDER BY title" , authorname, blog_name)
    else:
        return db.GqlQuery("SELECT * FROM Blog " +
            "WHERE authorname = :1 " + 
            "ORDER BY title", authorname)

def getBlogPostsQuery(authorname, blog_name, blog_post_name = None, tag_name = None):
    if blog_post_name:
        return db.GqlQuery("SELECT * FROM Blogpost " +
            "WHERE authorname = :1 AND blog = :2 AND title = :3 " +
            "ORDER BY date DESC", authorname, blog_name, blog_post_name)
    elif tag_name:
        return db.GqlQuery("SELECT * FROM Blogpost " +
            "WHERE authorname = :1 AND blog = :2 AND tags = :3 " +
            "ORDER BY date DESC", authorname, blog_name, tag_name)
    else:
        return db.GqlQuery("SELECT * FROM Blogpost " +
            "WHERE authorname = :1 AND blog = :2 " +
            "ORDER BY date DESC", authorname, blog_name)
def getBlogPostsQueryByID(blog_id):
    return db.GqlQuery("SELECT * FROM Blogpost " +
        "WHERE ")

def getUsername(userID):
    user_pref_query = db.GqlQuery("SELECT * FROM UserPref " +
        "WHERE userID = :1", userID)
    user_pref = user_pref_query.run(limit=1)

    for pref in user_pref:
        return pref.username
    return None


def to_link(str):
    new_link='<a href="'+str+'">'+str+'</a>'
    if str.endswith(".jpg") or str.endswith(".png") or str.endswith(".gif"):
        new_link = str
    return jinja2.Markup(new_link)

class UserPref(db.Model):
    userID = db.StringProperty(required=True)
    username = db.StringProperty(required=True)

class Blog(db.Model):
    authorname = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    urltitle = db.StringProperty(required=True)

class Blogpost(db.Model):
    authorname = db.StringProperty(required=True)
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
            username = getUsername(user.user_id())
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            username =''
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'username': username
        }   
    
        template = JINJA_ENVIRONMENT.get_template('404.html')
        self.response.write(template.render(template_values))

class HomePage(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()

        if user:
            username = getUsername(user.user_id())
            if not username:
                self.redirect('/username/')
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            username = ''
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = { 
            'user' : user,
            'username': username,
            'url': url,
            'url_linktext': url_linktext
        }   
    
        template = JINJA_ENVIRONMENT.get_template('home_page.html')
        self.response.write(template.render(template_values))

class UsernamePage(webapp2.RequestHandler):

    def isInvalid(self,username):
        invalidCharacters = re.compile('[[\w]*[\W]+[\w]*]*')
        return bool(invalidCharacters.search(username))

    def isTaken(self, username):
        user_pref_query = db.GqlQuery("SELECT * FROM UserPref " +
        "WHERE username = :1", username)
        user_pref = user_pref_query.run(limit=1)

        for pref in user_pref:
            return True
        return False

    def post(self):
        """Set a username"""
        username = self.request.get('username').strip()
        user = users.get_current_user()
        '''
        if no username entered
        if username is taken
        if username is already the username the user has
        if the username is invalid

        '''
        if not username or self.isInvalid(username):
            self.get('Please enter a valid username', username)
        elif self.isTaken(username):
            self.get('This username is already taken', username)
        else:
            userpref = UserPref(username=username, userID=user.user_id())
            userpref.put()
            self.redirect('/user/')

    def get(self, error='', username=''):
        user = users.get_current_user()

        if user:
            template_url= 'username_page.html'
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

            template_values = { 
                'user' : user,
                'url': url,
                'url_linktext': url_linktext,
                'error': error,
                'username': username
            } 

            template = JINJA_ENVIRONMENT.get_template(template_url)
            self.response.write(template.render(template_values))
        else:
            self.redirect('/')

class UserHome(webapp2.RequestHandler):
    def isInvalid(self,new_blog_name):
        invalidCharacters = re.compile('[^a-zA-Z0-9 ]+')
        return bool(invalidCharacters.search(new_blog_name))

    def post(self):
        """Create a new blog for the logged-in user."""
        new_blog_name = self.request.get('blog_title')
        user = users.get_current_user()
        username = getUsername(user.user_id())

        if new_blog_name:
            blog_name_query = getBlogsQuery(username, new_blog_name)
            duplicateBlogFound = bool(blog_name_query.count())

            if self.isInvalid(new_blog_name):
                error = new_blog_name+" is an invalid blog name"
                self.get(error)
            elif len(new_blog_name) > 30:
                error = new_blog_name+" is too long"
                self.get(error)
            elif duplicateBlogFound:
                error = 'You already have a blog titled '+new_blog_name
                self.get(error)
            else:
                new_blog_urltitle = new_blog_name.replace(' ','-')
                new_blog = Blog(authorname=username,title=new_blog_name,urltitle=new_blog_urltitle)
                new_blog.put()
                self.redirect('/blog/'+username+'/'+new_blog_urltitle+'/')
                
        else:
            self.redirect('/user/')

    def get(self,error=None):
        user = users.get_current_user()
        
        if user:
            username = getUsername(user.user_id())

            if not username:
                self.redirect('/username/')

            else:
                template_url= 'user_home_page.html'
                url = users.create_logout_url(self.request.uri)
                url_linktext = 'Logout'

                blog_query= getBlogsQuery(username)

                blogs = blog_query.run(limit=100)

                template_values = { 
                    'user' : user,
                    'username': username,
                    'url': url,
                    'url_linktext': url_linktext,
                    'blogs': blogs,
                    'error': error
                } 

                template = JINJA_ENVIRONMENT.get_template(template_url)
                self.response.write(template.render(template_values))
        else:
            self.redirect('/')

class BlogHome(webapp2.RequestHandler):

    def post(self, authorname, blog_urltitle, page_number):
        blog_name = blog_urltitle.replace('-',' ')
        blogpost_title = self.request.get('blogpost_title')
        blogpost_content = self.request.get('blogpost_content')
        user = users.get_current_user()
        username = getUsername(user.user_id())
        
        if blogpost_title and blogpost_content:

            blogpost_tags = self.request.get('blogpost_tags')
            tag_tokens = [tag.strip() for tag in blogpost_tags.split(',')]

            blogpost = Blogpost(authorname=username, title=blogpost_title, content=blogpost_content, blog=blog_name, tags=tag_tokens)
            blogpost.put()

            self.redirect('/blog/' + username + '/' + blog_urltitle + '/')
        else:
            self.redirect('/blog/' + username + '/' + blog_urltitle + '/')


    def get(self, authorname, blog_urltitle, page_number=0):
        blog_name = blog_urltitle.replace('-',' ')
        user = users.get_current_user()

        if page_number:
            ViewingPage = int(page_number)
        else:
            ViewingPage = 0


        if user:
            username = getUsername(user.user_id())
            if not username:
                self.redirect('/username/')
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

            blog_query = getBlogsQuery(username)
            blogs = blog_query.run(limit=1000)
        else:
            username = ''
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            blogs = []

        one_blog_query = getBlogsQuery(authorname, blog_name)

        blogFound = False
        owner = False
        authorname = "error"
        for b in one_blog_query.run(limit=1):
            blogFound = True
            owner = (user and (username == b.authorname))
            # owner = (str(user.user_id()) == str(b.authorID))
            authorname = b.authorname

        # if blogFound:
        blogpost_query = getBlogPostsQuery(authorname, blog_name)

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
            
        

        template_values = { 
            'user' : user,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'username': username,
            'blogs' : blogs,
            'blogposts' : blogposts,
            'blog_name': blog_name,
            'blog_urltitle': blog_urltitle,
            'authorname': authorname,
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

    def post(self, authorname, blog_urltitle, blogpost_name, mode):
        blog_name = blog_urltitle.replace('-',' ')

        user = users.get_current_user()
        username = getUsername(user.user_id())

        owner = False

        one_blog_query = getBlogsQuery(authorname, blog_name)

        one_blog = one_blog_query.run(limit=1)
        
        for blog in one_blog:

            owner = (user and (username == blog.authorname))

        edit = (mode == "edit" and owner == True)

        blogpost_query = getBlogPostsQuery(authorname, blog_name, blogpost_name)

        blogpost = blogpost_query.run(limit=1)
        new_title = self.request.get('blogpost_title')
        new_content = self.request.get('blogpost_content')
        tag_str = self.request.get('blogpost_tags')
        new_tags = [tag for tag in tag_str.split(',') if not tag.strip() == '']
    

        if edit and owner:
            for post in blogpost:
                post.update(new_title, new_content, new_tags)

        self.redirect('/post/'+authorname+'/'+blog_urltitle+'/'+new_title+"/view")

    def get(self, authorname, blog_urltitle, blogpost_name, mode):
        blog_name = blog_urltitle.replace('-',' ')
        user = users.get_current_user()

        owner = False

        if user:
            username = getUsername(user.user_id())
            if not username:
                self.redirect('/username/')
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

            blog_query = getBlogsQuery(username)
            blogs = blog_query.run(limit=1000)

        else:
            username = ''
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            blogs = []

        one_blog_query = getBlogsQuery(authorname, blog_name)

        one_blog = one_blog_query.run(limit=1)
        for blog in one_blog:
            owner = (user and (username == blog.authorname))
                
        edit = (mode == "edit" and owner)

        blog_tags_query = getBlogPostsQuery(authorname, blog_name)

        blogpost_query = getBlogPostsQuery(authorname, blog_name, blogpost_name)

        blog_tags=[]
        for post in blog_tags_query.run(limit=1000):
            for tag in post.tags:
                if tag not in blog_tags:
                    blog_tags.append(tag)
        blog_tags.sort()

        #not entering this loop after edit
        for post in blogpost_query.run(limit=1):
            post.content.split(' ')
            text_tokens = post.content.split(' ')
            for tok in text_tokens:
                if self.isLink(tok):
                    post.content=post.content.replace(tok,to_link(tok))
            blogpost = post

        template_values = { 
            'user' : user,
            'username': username,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'blogs' : blogs,
            'blogpost' : blogpost,
            'blog_name': blog_name,
            'blog_urltitle': blog_urltitle,
            'authorname': authorname,
            'one_blog': one_blog,
            'owner' : owner,
            'blog_tags' : blog_tags,
            'edit' : edit
        } 

        template = JINJA_ENVIRONMENT.get_template("blog_post_page.html")
        self.response.write(template.render(template_values))

class TagSearchPage(webapp2.RequestHandler):

    def get(self, authorname, blog_urltitle, tag_name, page_number=0):
        blog_name = blog_urltitle.replace('-',' ')
        if page_number:
            ViewingPage = int(page_number)
        else:
            ViewingPage = 0

        user = users.get_current_user()

        owner = False

        if user:
            username = getUsername(user.user_id())
            if not username:
                self.redirect('/username/')
            log_in_out_url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

            blog_query = getBlogsQuery(username)
            blogs = blog_query.run(limit=1000)
        else:
            username = ''
            template_url = 'home_page.html'
            log_in_out_url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            blogs = []

        one_blog_query = getBlogsQuery(authorname, blog_name)

        one_blog = one_blog_query.run(limit=1)

        for blog in one_blog:
            owner = (user and (username == blog.authorname))
        
        blogpost_query = getBlogPostsQuery(authorname, blog_name, None, tag_name)

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

        blog_tags_query = getBlogPostsQuery(authorname, blog_name) 

        blog_tags=[]

        for post in blog_tags_query.run(limit=1000):
            for tag in post.tags:
                if tag not in blog_tags:
                    blog_tags.append(tag)
        blog_tags.sort()

        template_values = { 
            'user' : user,
            'username': username,
            'url': log_in_out_url,
            'url_linktext': url_linktext,
            'blogs' : blogs,
            'blogposts' : blogposts,
            'blogpost_content': blogpost_content,
            'blog_name': blog_name,
            'blog_urltitle': blog_urltitle,
            'authorname': authorname,
            'one_blog': one_blog,
            'tag_name' : tag_name,
            'blog_tags' : blog_tags,
            'owner' : owner,
            'moreposts': moreposts,
            'page_counter': ViewingPage
        } 

        template = JINJA_ENVIRONMENT.get_template("tag_search_page.html")
        self.response.write(template.render(template_values))

# need more specific routes so that Error handling works
# .* is not acceptable, what if the blog doesn't exist and someone tries to access that page

application = webapp2.WSGIApplication([
    ('/', HomePage),
    (r'/user[/]?', UserHome),
    (r'/username[/]?', UsernamePage),
    (r'/blog/(.*)/(.*)/(.*)', BlogHome), 
    #(r'/blog/([^/]*)/([^/]*)[/(.*)|/]?', BlogHome), 
    # these urls should be supported and not go to 404 page
    # /blog/authorname/blogname
    # /blog/authorname/blogname/
    # /blog/authorname/blogname/pagenumber
    (r'/post/(.*)/(.*)/(.*)/(.*)', BlogpostPage),
    (r'/search/(.*)/(.*)/(.*)/(.*)', TagSearchPage)
], debug=True)
