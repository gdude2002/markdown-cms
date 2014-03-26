__author__ = 'Gareth Coles'

from bottle import static_file, abort
from internal.util import log


class Routes(object):

    def __init__(self, app, manager):
        self.app = app
        self.manager = manager

        app.route("/static/<path:path>", ["GET", "POST"], self.static)
        app.route("/css/<path:path>", ["GET", "POST"], self.static_blog_css)
        app.route("/js/<path:path>", ["GET", "POST"], self.static_blog_js)
        app.route("/static/", ["GET", "POST"], self.static_403)
        app.route("/static", ["GET", "POST"], self.static_403)
        app.route("/.well-known/keybase.txt", ["GET", "POST"],
                  self.static_keybase_txt)

        log("Static routes set up.")

    def static(self, path):
        return static_file(path, root="static")

    def static_blog_css(self, path):
        return static_file(path, root="static/blog/css")

    def static_blog_js(self, path):
        return static_file(path, root="static/blog/js")

    def static_keybase_txt(self, path):
        return static_file("keybase.txt", root="static")

    def static_403(self):
        abort(403, "You may not list the static files.")
