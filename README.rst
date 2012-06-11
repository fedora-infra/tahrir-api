tahrir-api
==========

API for interacting with the Tahrir database
Based on the `Tahrir <https://github.com/ralphbean/tahrir>`_ database model
written by `Ralph Bean <https://github.com/ralphbean>`_. There are two classes
that can be used in this module. The first is TahrirDatabase class located in
tahrir_api.dbapi and the second is the database model located in
tahrir_api.model. The TahrirDatabase class is a high level way to interact with
the database. The model is used for a slightly more low level way of interacting
with the database. It allows for custom interactions with the database without
having to use the TahrirDatabase class.
