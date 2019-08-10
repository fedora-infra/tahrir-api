Tahrir-API
==========

API for interacting with the Tahrir database.  Based on the `Tahrir
<https://github.com/fedora-infra/tahrir>`_ database model written by `Ralph
Bean <https://github.com/ralphbean>`_. There are two classes that can be used
in this module. The first is the ``TahrirDatabase`` class located in
``tahrir_api.dbapi`` and the second is the database model located in
``tahrir_api.model``. The ``TahrirDatabase`` class is a high level way to
interact with the database. The model is used for a slightly more low level way
of interacting with the database. It allows for custom interactions with the
database without having to use the ``TahrirDatabase`` class.

Creating a Badge
================

This is an example of creating a badge via Tahrir-API:

.. code-block:: python

    from tahrir_api.dbapi import TahrirDatabase


    db = TahrirDatabase('backend://badges:badgesareawesome@localhost/badges')

    origin = 'http://foss.rit.edu/badges'
    issuer_name = 'FOSS@RIT'
    org = 'http://foss.rit.edu'
    contact = 'foss@rit.edu'

    issuer_id = db.add_issuer(origin, issuer_name, org, contact)

    badge_name = 'fossbox'
    image = 'http://foss.rit.edu/files/fossboxbadge.png'
    desc = 'Welcome to the FOSSBox. A member is you!'
    criteria = 'http://foss.rit.edu'

    db.add_badge(badge_name, image, desc, criteria, issuer_id)


Awarding a Badge
================

This is an example of awarding a badge via Tahrir-API:

.. code-block:: python

    from tahrir_api.dbapi import TahrirDatabase


    db = TahrirDatabase('backend://badges:badgesareawesome@localhost/badges')

    badge_id = 'fossbox'
    person_email = 'person@email.com'
    issued_on = None

    db.add_person(person_email)
    db.add_assertion(badge_id, person_email, issued_on)


Development
===========

Set-up your env
---------------
Install helper

.. code-block:: bash

    $ sudo dnf install -y python3-virtualenvwrapper  # RedHat-based OS

Build your virtual env

.. code-block:: bash

    $ export WORKON_HOME=$HOME/.virtualenvs
    $ mkvirtualenv tahrir-api

Connect w/ your virutal env

.. code-block:: bash

    $ workon tahrir-api
    (tahrir-api)$

Install
-------
Requirements

.. code-block:: bash

    (tahrir-api)$ pip install -r requirements.txt

Project installation

.. code-block:: bash

    (tahrir-api)$ python setup.py develop

Happy hacking!

Run the tests
-------------

You can run the tests with ``tox``

.. code-block:: bash

    (tahrir-api)$ pip install tox
    (tahrir-api)$ tox
