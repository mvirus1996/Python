import tornado
from tornado.web import RequestHandler
import os
import pandas as pd


currentDir = os.path.join(os.getcwd(), 'data')

# could define get_user_async instead
def get_user(request_handler):
    return request_handler.get_cookie("user")

# could also define get_login_url function (but must give up LoginHandler)
login_url = "/login"

# optional login page for login_url
class LoginHandler(RequestHandler):
    uname = ""
    def get(self):
        try:
            errormessage = self.get_argument("error")
        except Exception:
            errormessage = ""
        self.render("login.html", errormessage=errormessage)

    def check_permission(self, name, pasw):
        logData = pd.read_csv(os.path.join(currentDir, 'Credentials.csv'), error_bad_lines=False)
    
        logData.set_index('name', inplace=True)
        getName = True
        try:
            logData.loc[name, 'pasw']
        except:
            getName = False
        if getName and logData.loc[name, 'pasw'] == pasw:
            self.uname = name
            return True
        return False

    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        if username == "":
            error_msg = "?error=" + tornado.escape.url_escape("Enter Username")
            self.redirect(login_url + error_msg)
        elif password == "":
            error_msg = "?error=" + tornado.escape.url_escape("Enter Password")
            self.redirect(login_url + error_msg)
        else:
            auth = self.check_permission(username, password)
            if auth:
                self.set_current_user(username)
                self.redirect(self.get_argument("next", "/"))
            else:
                error_msg = "?error=" + tornado.escape.url_escape("Invalid Credentials")
                self.redirect(login_url + error_msg)

    def set_current_user(self, user):
        if user:
            print("tornado.escape.json_encode(user) :1 ",tornado.escape.json_encode(user))
            self.clear_cookie("user")
            self.set_cookie("user", tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")

# optional logout_url, available as curdoc().session_context.logout_url
logout_url = "/logout"

# optional logout handler for logout_url
class LogoutHandler(RequestHandler):

    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))