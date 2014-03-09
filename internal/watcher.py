__author__ = 'Gareth Coles'

from watchdog.events import FileSystemEventHandler


class EventHandler(FileSystemEventHandler):

    def __init__(self, callback):
        self.callback = callback

    def on_any_event(self, event):
        super(EventHandler, self).on_any_event(event)
        self.callback(event)
