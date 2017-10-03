#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to keep random utils. 

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


def autocommit(func):
    """ 
    A decorator that autocommits after API calls unless
    configured otherwise.
    """

    def _wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if self.autocommit:
            self.session.commit()
        return result

    _wrapper.__name__ = func.__name__
    _wrapper.__doc__ = func.__doc__
    return _wrapper


def convert_name_to_id(name):
    """
    Convert a badge name into a valid badge ID.

    :param name: The badge name to convert to an ID
    :type name: string
    """
    badge_id = name.lower().replace(" ", "-")
    bad = ['"', "'", '(', ')', '*', '&', '?']
    replacements = dict(zip(bad, [''] * len(bad)))
    for a, b in replacements.items():
        badge_id = badge_id.replace(a, b)
    return badge_id


def bytes_(s, encoding='utf-8', errors='strict'):
    """
    If ``s`` is an instance of ``text_type``, return
    ``s.encode(encoding, errors)``, otherwise return ``s``
    """
    if not isinstance(s, bytes) and s is not None:
        s = s.encode(encoding, errors)
    return s
