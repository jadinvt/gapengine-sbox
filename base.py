import webapp2

class BaseHandler(webapp2.RequestHandler):
    def write(self, template='', dictionary={'title':'','post':'','error':''}):
        self.response.out.write(template %  dictionary)