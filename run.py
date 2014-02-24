# coding=utf-8
__author__ = "Gareth Coles"

from internal.manager import Manager

manager = Manager()

application = app = manager.get_app()

if __name__ == "__main__":
    manager.start()
