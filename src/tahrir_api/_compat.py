#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six import text_type


def to_unicode(s, encoding='utf-8', err='strict'):
    """
    Decode a byte sequence and unicode result
    """
    if not isinstance(s, text_type) and s is not None:
        s = s.decode(encoding, err)
    return s
text_ = to_unicode


def bytes_(s, encoding='utf-8', errors='strict'):
    """
    If ``s`` is an instance of ``text_type``, return
    ``s.encode(encoding, errors)``, otherwise return ``s``
    """
    if not isinstance(s, bytes) and s is not None:
        s = s.encode(encoding, errors)
    return s
