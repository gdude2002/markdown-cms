__author__ = 'Gareth Coles'

import logging
import os
import yaml

from bottle import request, response, redirect, abort
from bottle import mako_template as template
from watchdog.observers import Observer

from internal.util import log, parse_markdown
from internal.watcher import EventHandler


class Routes(object):

    app = None
    config = {}  # Dict-like
    latest_entries = []
    parsed_entries = {}

    all_pages = {}
    parsed_pages = {}

    watcher = None

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

        self.watcher = Observer()
        handler = EventHandler(self.watcher_callback)
        self.watcher.schedule(handler, "blog", recursive=True)
        self.watcher.start()

        log("Blog routes set up.")

    def watcher_callback(self, event):

        if event.is_directory or event.src_path.endswith("~"):
            # The latter is for Vim support
            return

        if event.event_type != "moved":
            if event.src_path.endswith(("___jb_bak___", "___jb_old___")):
                # IntelliJ IDE support
                return
        else:
            if event.dest_path.endswith(("___jb_bak___", "___jb_old___")):
                # IntelliJ IDE support
                return

        path = os.path.relpath(event.src_path).replace("\\", "/")
        split_path = path.split("/")
        split_path.pop(0)  # blog

        if split_path[-1].startswith(".") or not "." in split_path[-1]:
            # Vim and dot-files support
            return

        if event.event_type == "modified":
            log("Modified: %s" % path, logging.INFO)

            if split_path[0] == "config.yml":
                self.reload_config()
            elif split_path[0] == "entries":
                self.reload_entry(split_path[1].rstrip(".md"))
            elif split_path[0] == "pages":
                self.reload_page(split_path[1])

# Old stuff, not needed atm

# elif event.event_type == "moved":
#     destination = os.path.relpath(event.dest_path).replace("\\", "/")
#     dest_split = destination.split("/")
#     dest_split.pop(0)  # blog
#
#     if dest_split[-1].startswith(".") or not "." in dest_split[-1] or \
#        dest_split[-1].endswith("~"):
#         # Vim and dot-files support
#         return
#
#     log("Moved: %s -> %s" % (path, destination), logging.INFO)
# elif event.event_type == "created":
#     log("Created: %s" % path, logging.INFO)
# elif event.event_type == "deleted":
#     log("Deleted: %s" % path, logging.INFO)

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

    def reload_config(self):
        self.config = yaml.load(open("blog/config.yml", "r"))
        config_entries = self.config["entries"][:]
        config_entries.reverse()
        self.config["reversed_entries"] = config_entries

        for entry in self.parsed_entries.keys()[:]:
            if entry not in self.config["entries"]:
                del self.parsed_entries[entry]

        for entry in self.config["entries"]:
            if entry not in self.parsed_entries:
                self.reload_entry(entry, False)

        self.reload_entry(None)

    def reload_entry(self, entry, recount_latest=True):
        base_url = "/blog/entry/%s"

        if not os.path.exists("blog/entries/%s.md" % entry):
            if entry in self.parsed_entries:
                log("Entry deleted: %s" % entry)
                del self.parsed_entries[entry]
                return

        if entry in self.config["entries"]:
            try:
                markdown = parse_markdown("blog/entries/%s.md" % entry)
            except Exception as e:
                log("Unable to parse '%s': %s" % (entry, e), logging.WARN)
            else:
                self.parsed_entries[entry] = markdown
                log("Parsed entry: %s" % entry, logging.INFO)

        if recount_latest:
            self.latest_entries = []
            for i in range(0, 9):
                try:
                    entry = self.config["reversed_entries"][i]
                    markdown = self.parsed_entries[entry]
                    title = markdown.Meta["title"][0]
                    self.latest_entries.append({"title": title,
                                                "url": base_url % entry})
                except IndexError:
                    break  # No more entries

    def reload_page(self, filename):
        if filename.endswith(".md"):
            name = filename.rsplit(".", 1)[0]
            friendly = name.replace("_", " ").title()
            if not os.path.exists("blog/pages/%s" % filename):
                if friendly in self.all_pages:
                    del self.all_pages[friendly]
                    log("Page deleted: %s" % friendly, logging.INFO)
                    return
            try:
                markdown = parse_markdown("blog/pages/%s" % filename)
            except Exception as e:
                log("Unable to parse '%s': %s" % (name, e), logging.WARN)
            else:
                self.all_pages[friendly] = "/blog/page/%s" % name
                self.parsed_pages[name] = markdown
                log("Parsed page: %s" % name, logging.INFO)

    def _reload(self):
        self.reload_config()

        log("Parsing all pages..", logging.INFO)

        for filename in os.listdir("blog/pages"):
            if filename.endswith(".md"):
                name = filename.rsplit(".", 1)[0]
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
