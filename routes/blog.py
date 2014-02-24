__author__ = 'Gareth Coles'

import logging
import os

from bottle import request, response, redirect, abort
from bottle import mako_template as template
from internal.util import log, parse_markdown

import yaml


class Routes(object):

    app = None
    config = {}  # Dict-like
    latest_entries = []
    parsed_entries = {}

    all_pages = {}
    parsed_pages = {}

    def __init__(self, app, manager):
        self.app = app
        self.manager = manager

        self._reload()

        app.route("/blog", "GET", self.blog)
        app.route("/blog/", "GET", self.blog)

        app.route("/blog/page", "GET", self.blog_redirect)
        app.route("/blog/page/<page>", "GET", self.blog_page)
        app.route("/blog/page/<page>/", "GET", self.blog_page)

        app.route("/blog/entry", "GET", self.blog_redirect)
        app.route("/blog/entry/<entry>", "GET", self.blog_entry)
        app.route("/blog/entry/<entry>/", "GET", self.blog_entry)

        app.route("/blog/reload/<password>", "GET", self.reload)

        log("Blog routes set up.")

    def blog(self):
        if self.config["frontpage"]["mode"] == "entry":
            filename = self.config["frontpage"]["entry"]
        else:
            filename = self.config["entries"][-1]
        markdown = self.parsed_entries[filename]
        return template("templates/blog/index.html", content=markdown,
                        entries=self.get_entries(), pages=self.get_pages())

    def blog_page(self, page):
        if not page:
            redirect("/blog", 303)
        else:
            if page in self.all_pages:
                markdown = self.all_pages[page]
            elif page.lower() in self.parsed_pages:
                markdown = self.parsed_pages[page.lower()]
            else:
                response.status = 404
                return template("templates/blog/404.html",
                                entries=self.get_entries(),
                                pages=self.get_pages())

            return template("templates/blog/page.html", content=markdown,
                            entries=self.get_entries(), pages=self.get_pages())

    def blog_entry(self, entry):
        if not entry:
            redirect("/blog", 303)
        else:
            entry = entry.lower()
            replaced = entry.replace("_", " ")

            if entry in self.parsed_entries:
                markdown = self.parsed_entries[entry]
            elif replaced in self.parsed_entries:
                markdown = self.parsed_entries[replaced]
            else:
                response.status = 404
                return template("templates/blog/404.html",
                                entries=self.get_entries(),
                                pages=self.get_pages())

            return template("templates/blog/entry.html", content=markdown,
                            entries=self.get_entries(), pages=self.get_pages())

    def blog_redirect(self):
        redirect("/blog", 303)

    def get_entries(self):
        return self.latest_entries

    def get_pages(self):
        return self.all_pages

    def _reload(self):
        self.config = yaml.load(open("blog/config.yml", "r"))
        config_entries = self.config["entries"][:]
        config_entries.reverse()
        self.config["reversed_entries"] = config_entries

        self.latest_entries = []
        base_url = "/blog/entry/%s"

        log("Parsing all entries..", logging.INFO)
        for entry in self.config["entries"]:
            try:
                markdown = parse_markdown("blog/entries/%s.md" % entry)
            except Exception as e:
                log("Unable to parse '%s': %s" % (entry, e), logging.WARN)
            else:
                self.parsed_entries[entry] = markdown
                log("Parsed entry: %s" % entry, logging.INFO)
        log("All entries parsed.", logging.INFO)

        for i in range(0, 9):
            try:
                entry = self.config["reversed_entries"][i]
                markdown = self.parsed_entries[entry]
                title = markdown.Meta["title"][0]
                self.latest_entries.append({"title": title,
                                            "url": base_url % entry})
            except IndexError:
                break  # No more entries

        log("Parsing all pages..", logging.INFO)

        for filename in os.listdir("blog/pages"):
            if filename.endswith(".md"):
                name = filename.split(".")[0]
                friendly = name.replace("_", " ").title()
                try:
                    markdown = parse_markdown("blog/pages/%s" % filename)
                except Exception as e:
                    log("Unable to parse '%s': %s" % (name, e), logging.WARN)
                else:
                    self.all_pages[friendly] = "/blog/page/%s" % name
                    self.parsed_pages[name] = markdown
                    log("Parsed page: %s" % name, logging.INFO)

        log("All pages parsed.", logging.INFO)

    def reload(self, password):
        if password == self.config["password"]:
            self._reload()
            abort(200, "Configuration reloaded successfully!")
        else:
            abort(404, "Not found: '%s'" % request.path)
