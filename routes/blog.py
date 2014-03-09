__author__ = 'Gareth Coles'

import shelve
import logging
import os
import pickle

from lockfile import LockFile

from bottle import request, response, redirect, abort
from bottle import mako_template as template
from internal.util import log, parse_markdown, log_error

import yaml


class Routes(object):

    app = None
    config = shelve.Shelf  # Dict-like
    latest_entries = shelve.Shelf
    parsed_entries = shelve.Shelf

    all_pages = shelve.Shelf
    parsed_pages = shelve.Shelf

    lock = LockFile("lockfile.lock")

    def __init__(self, app, manager):
        self.app = app
        self.manager = manager

        try:
            os.makedirs("cache")
        except:
            pass

        self.config = shelve.open("cache/config", "c", writeback=True)
        self.latest_entries = shelve.open("cache/entries-latest", "c",
                                          writeback=True)
        self.parsed_entries = shelve.open("cache/entries-parsed", "c",
                                          writeback=True)
        self.all_pages = shelve.open("cache/pages-all", "c", writeback=True)
        self.parsed_pages = shelve.open("cache/pages-parsed", "c",
                                        writeback=True)

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

    def do_sync(self):
        self.config.close()
        self.latest_entries.close()
        self.parsed_entries.close()
        self.all_pages.close()
        self.parsed_pages.close()

        self.config = shelve.open("cache/config", "c", writeback=True)
        self.latest_entries = shelve.open("cache/entries-latest", "c",
                                          writeback=True)
        self.parsed_entries = shelve.open("cache/entries-parsed", "c",
                                          writeback=True)
        self.all_pages = shelve.open("cache/pages-all", "c", writeback=True)
        self.parsed_pages = shelve.open("cache/pages-parsed", "c",
                                        writeback=True)

    def blog(self):
        self.do_sync()
        if self.config["frontpage"]["mode"] == "entry":
            filename = self.config["frontpage"]["entry"]
        else:
            filename = self.config["entries"][-1]
        markdown = self.parsed_entries[filename]
        return template("templates/blog/index.html", content=markdown,
                        entries=self.get_entries(), pages=self.get_pages())

    def blog_page(self, page):
        self.do_sync()
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
        self.do_sync()
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
        return self.latest_entries["latest"]

    def get_pages(self):
        return self.all_pages

    def hacky_strip(self, obj):
        funcs = dir(obj)[:]

        for func in funcs:
            if not func.startswith("__") \
               and not func.endswith("__"):
                try:
                    if not isinstance(getattr(obj, func),
                                      str):
                        if not func in ["Meta", "html"]:
                            delattr(obj, func)

                except AttributeError:
                    pass

        return obj

    def _reload(self):
        with self.lock:
            config = yaml.load(open("blog/config.yml", "r"))
            self.config["entries"] = config["entries"]
            self.config["frontpage"] = config["frontpage"]
            self.config["password"] = config["password"]
            config_entries = self.config["entries"][:]
            config_entries.reverse()
            self.config["reversed_entries"] = config_entries

            self.latest_entries["latest"]= []
            base_url = "/blog/entry/%s"

            log("Parsing all entries..", logging.INFO)
            for entry in self.config["entries"]:
                try:
                    markdown = parse_markdown("blog/entries/%s.md" % entry)
                except Exception as e:
                    log_error("Unable to parse '%s': %s" % (entry, e))
                else:
                    markdown = self.hacky_strip(markdown)

                    self.parsed_entries[entry] = markdown
                    log("Parsed entry: %s" % entry, logging.INFO)
            log("All entries parsed.", logging.INFO)

            for i in range(0, 9):
                try:
                    entry = self.config["reversed_entries"][i]
                    markdown = self.parsed_entries[entry]
                    title = markdown.Meta["title"][0]
                    self.latest_entries["latest"].append({"title": title,
                                                          "url": base_url %
                                                          entry})
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

                        markdown = self.hacky_strip(markdown)

                        self.parsed_pages[name] = markdown
                        log("Parsed page: %s" % name, logging.INFO)

            self.do_sync()

            log("All pages parsed.", logging.INFO)

    def reload(self, password):
        if password == self.config["password"]:
            self._reload()
            abort(200, "Configuration reloaded successfully!")
        else:
            abort(404, "Not found: '%s'" % request.path)
