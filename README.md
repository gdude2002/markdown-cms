markdown-cms
============

A CMS powered by Python with Bottle and using Markdown files for content.
It's designed to be fast, easy to use and easy to configure. It's also fully
compatible with your WSGI server!

Markdown CMS compiles the Markdown files into memory at runtime. This is to
save on processing time later - they aren't compiled every time an entry
is accessed. Additionally, files are reloaded when they've been modified,
so you shouldn't have to worry about reloading them manually.

As nobody who's involved in this project is a designer, I've decided to go
with a standard theme from HTML5 UP, which has been modified slightly
to work with Mako, the templating engine we're using. Naturally, HTML5 UP
reserves all rights to the design. You will absolutely want to change the
templates at the moment; they will be more configurable later on.

Setting up
==========

Markdown CMS requires the following:
* Python 2.7 (32-bit only if you're on Windows)
    * If you're on Windows, [add Python to your PATH](http://www.anthonydebarros.com/2011/10/15/setting-up-python-in-windows-7/)
* Pip (Use
    [get-pip.py](https://raw.github.com/pypa/pip/master/contrib/get-pip.py)
    if you're on Windows)

After this, open a console in the same folder you cloned this repo to, and run
`pip install -r requirements.txt` to install all other dependencies.

Configuration
=============

So far, all configuration is in one single file: `blog/config.yml`.
It's not very big, but it is very important, so don't forget about it.
Let's work from the bottom-up..

* `password` - This is a configurable password for reloading the configuration
    and recompiling all the Markdown files - You shouldn't need to do this
    manually, however.
* `frontpage` - Settings that relate to which entry is shown on the front page.
    * `mode` - This can be either `latest` or `entry`; use the latter if you just
        want to show a specific entry all the time.
    * `entry` - Only applies when the mode is set to `entry`, this is the
        name of the entry to display on the front page.
* `entries` - A list of entries, starting with your earliest entry, without the
    `.md` suffix. You can order this however you wish; but we recommend that you
    put your earliest entry at the top and latest entry at the bottom, in
    chronological order.

Running
=======

You've got two options for running this (Or at least, two that the CMS was
designed for).

* For development only, run `run.py` directly using Python.
    * You can also create a development.yml file in the main directory if you want
        to change the running defaults.
        * `host` (Defaults to **127.0.0.1**) - The hostname to listen on
        * `port` (Defaults to **8080**) - The port to listen on
        * `server` (Defaults to **cherrypy**) - The
            [Bottle adapter](http://bottlepy.org/docs/dev/deployment.html#switching-the-server-backend)
            to use
    * You should **NEVER** use this in production, all webapps should be run by uWSGI or Gunicorn
        or some other master process that can deal with subthreading and subprocessing the webapp.
* For production, use uWSGI and Nginx.
    * Files are watched for changes and reloaded automatically.
        * Please note that you need to
            [enable threads](http://uwsgi-docs.readthedocs.org/en/latest/Options.html#enable-threads)
            for this to work.

Usage
=====

Markdown CMS is split into two types of content: blog entries and static pages.
They're both written in a slightly modified version of Markdown, which will be
explained later on.

Blog entries
------------

Blog entries are defined in `.md` files in the `blog/entries` folder. Entries
require the following metadata.

* `Title` - The title of the post.
    * This is also in the page title in the default template.
* `Description` - A short line, to be displayed under the post.
* `Date` - Not yet used. Doesn't have to be any special format, use whatever
    you like.

The filename of your entry `.md` files (Specifically, the part before the `.md`)
will also be what is used in the URL to your file and how you refer to it in
your configuration. For example, if I create an entry named `welcome.md`, then
it will be accessible at `http://domain:port/blog/entry/welcome`.

The rest of your `.md` file will be the content of your entry, and will be
displayed as such.

Static pages
------------

Static pages are listed in the secondary navigation bar (Below the main one
in the bundled templates). They are designed to be separate from normal entries,
their own first-class citizens if you will. They are defined in `.md` files in
the `blog/pages` folder, and require the following metadata.

* `Title` - The page title, displayed as a header on the page.
    * This is also in the page title in the default template.

The filename of your page `.md` files (Specifically, the part before the `.md`)
will also be what is used in the URL to your file and how it is displayed in
the navigation. If the filename contains any underscores, they are converted
to spaces, and then the filename is converted to title case. For example, if
I create a page named `sample_page.md`, it will be displayed in the navigation
as "Sample Page", and will be accessible at `http://domain:port/blog/page/sample_page`.

The rest of your `.md` file will be the content of your page, and will be
displayed as such.

Differences from standard Markdown (or what you may be used to)
---------------------------------------------------------------

Markdown CMS uses the Python [Markdown](pythonhosted.org/Markdown/) module to
compile its Markdown files. We've also decided to enable most of the extras
that are available in that package. The changes from what you may be used to are
as follows.

You can find the standard Markdown syntax documentation over at
[Daring Fireball](daringfireball.net/projects/markdown/syntax).

* As per the specs, indents for lists, etc must always be one tab or four spaces
    wide. GitHub and other sites allow arbitrary numbers of spaces; this is considered
    a bug!
* Abbreviations: Any defined abbreviations are wrapped within the relevant <abbr> tags.
    * Abbreviations are defined at the bottom of Markdown files, as follows: `*[ABBR]: Abbreviation`.
    * For example: `*[HTML]: Hyper Text Markup Language`
* Admonitions
    * These are pretty complicated, best to read about it [here](http://pythonhosted.org/Markdown/extensions/admonition.html).
* Attribute lists
    * This one is also complicated, read about it [here](http://pythonhosted.org/Markdown/extensions/attr_list.html).
* CodeHilite
    * Requires Pygments and some special CSS, see [here](http://pythonhosted.org/Markdown/extensions/code_hilite.html).
* Definition lists
    * These are defined as follows:
        ```
        Orange
        :    The fruit of an evergreen tree of the genus Citrus

        Lemon
        :    An explosive fruit, popularized by the late Cave Johnson.```
* Fenced code blocks
    * These help overcome a few limitations of indented code blocks. It also
        supports syntax highlighting (provided your template has CSS classes for
        it) and emphasized lines. [See here](http://pythonhosted.org/Markdown/extensions/fenced_code_blocks.html) for more info.
        ```
        A paragrah, introducing:

        [~~~~~~~~~~~~~] Remove the [] in your documents, it turns out GitHub also supports these.
        Some code
        [~~~~~~~~~~~~~]

        [~~~~~~~~~~~~~].python hl_lines="1 3"
        # This line is emphasized
        # This line isn't
        # This line is emphasized
        [~~~~~~~~~~~~~]
        ```
    * This also supports GitHub's backtick syntax (\`\`\`).
* Footnotes
    * If you've used Wikipedia, you know what these are.
        ```
        Footnotes[^1] have a label[^@#$%] and the footnote's content.

        [^1]: This is a footnote content.
        [^@#$%]: A footnote with the label: "@#$%".
        ```
* HTML embedding
    * You can add any block of HTML to your Markdown document and it will be included
        in the output. You can also add `markdown="1"` to block-level elements if
        you also want their content to be parsed as Markdown. For example:
        ```
        Input:
            <div markdown="1">
                This is *true* markdown text.
            </div>

        Output:
            <div>
                <p>This is <em>true</em> markdown text.</p>
            </div>
        ```
* Meta-Data
    * This is mostly used within the code, but you may want to know how it works for your templates.
        You can find information on this [here](http://pythonhosted.org/Markdown/extensions/meta_data.html).
* Sane lists
    * This makes Markdown lists less surprising. They should work how you'd expect, but if you
        find that something weird is going on, refer [here](http://pythonhosted.org/Markdown/extensions/sane_lists.html).
* SmartyPants
    * This converts various ASCII sequences with HTML entities. You can find the table of them
        [here](http://pythonhosted.org/Markdown/extensions/smarty.html), but note that
        "double quotes" won't end up converted, so that the extension doesn't break embedded
        HTML.
* Tables
    * Yep, tables too.
        ```

        First Header  | Second Header
        ------------- | -------------
        Content Cell  | Content Cell
        Content Cell  | Content Cell
        ```
* Table of Contents
    * Generates a table of contents based on the headers in your Markdown document.
        You can define one by adding `[TOC]` anywhere in your document. It also
        supports a CSS class, so see [here](http://pythonhosted.org/Markdown/extensions/toc.html)
        for information for your templates.
* WikiLinks
    * Simply, any `[[bracketed]]` word is converted to a relative link. If you use
        a space, it will be converted to an underscore in the link, but the label
        will still show the space.

Reloading the server
--------------------

To reload the server, simply go to the following URL: `http://domain:port/blog/reload/password`,
replacing "password" with the password you supplied in the configuration above.

**Note:** You no longer actually have to do this. The CMS will watch all the files for changes and reload
them automatically.