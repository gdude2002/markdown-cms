__author__ = 'Gareth Coles'

import logging
import markdown
import sys

logging.basicConfig(
    format="%(asctime)s | %(levelname)8s | %(message)s",
    datefmt="%d %b %Y - %H:%M:%S",
    level=(logging.DEBUG if "--debug" in sys.argv else logging.INFO))


def log(message, level=logging.DEBUG):
    logging.log(level, message)


def log_error(message):
    logging.exception(message)


def log_request(request, message, level=logging.DEBUG):
    ip = request.remote_addr
    log("[%s] %s" % (ip, message), level)


def parse_markdown(path):
    md = markdown.Markdown(extensions=["extra", "admonition", "codehilite",
                                       "headerid", "meta",  # "nl2br",
                                       "sane_lists",
                                       "smarty", "toc", "wikilinks"],
                           output_format="html5")
    fh = open(path, "r")
    data = fh.read()
    fh.close()
    del fh

    html = md.convert(data)
    html = html.replace("&ldquo;", "\"")
    html = html.replace("&rdquo;", "\"")

    md.html = html

    return md
