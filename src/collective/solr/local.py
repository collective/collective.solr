# -*- coding: utf-8 -*-
from threading import local


# a thread-local object holding data for the queue
localData = local()
marker = []


def getLocal(name, factory=lambda: None):
    """ get named thread-local value and optionally initialize it """
    value = getattr(localData, name, marker)
    if value is marker:
        value = factory()
        setLocal(name, value)
    return value


def setLocal(name, value):
    """ set a value for the named thread-local variable """
    setattr(localData, name, value)
