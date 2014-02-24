__author__ = 'Gareth Coles'

from bottle import redirect


class Routes(object):

    def __init__(self, app, manager):
        self.app = app
        self.manager = manager

        app.route("/", "GET", self.index)

    def index(self):
        redirect("/blog", 303)
