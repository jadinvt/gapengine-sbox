import unittest
import settings
import string, random
import urllib
import urllib2
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup

base_url = "http://localhost:8080"
blog_path = "/blog"
blog_new_page = blog_path + "/newpost"
redirect_codes = (300, 301, 302, 303, 307)

class RedirectCatchHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code       
        return infourl
    http_error_301 = http_error_303 = http_error_307 = http_error_302


class BlogInterfaceTests(unittest.TestCase):
    
    def setUp(self):
        if settings.DEBUG:
            print "Setting up"
    
    def tearDown(self):
        if settings.DEBUG:
            print "Tearing down"
            
    def get_random_string(self, length=50):
        return ''.join(random.choice(string.letters) for i in xrange(100))
    
    def dummy_test(self):        
        self.assertTrue(True)
    
    def site_up_test(self):
        page = urlopen(base_url)
        self.assertEqual(page.getcode(), 200) 
    
    def blog_front_page_up_test(self):
        page = urlopen(base_url+blog_path)     
        self.assertEqual(page.getcode(), 200)
        
    def blog_new_page_up_test(self):    
        subject = self.get_random_string()
        content = self.get_random_string()
        opener = urllib2.build_opener(RedirectCatchHandler())
        page = opener.open(base_url+blog_new_page, "subject=%s&content=%s"%
                       (subject, content))
        self.assertTrue(page.getcode() in redirect_codes)
        if settings.DEBUG:
            print "redirct to %s"%(page.geturl())

        page = urlopen(page.headers.dict['location'])
        self.assertEqual(page.getcode(), 200)
        html = page.read()
        soup = BeautifulSoup(html)
        if settings.DEBUG:
            print "find %s %s %s"%(soup.text, subject, content)
        
        self.assertGreater(soup.text.rfind(subject), -1)
        self.assertGreater(soup.text.rfind(content), -1)
        