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


Creating a Badge
================
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

.. code-block:: python

    from tahrir_api.dbapi import TahrirDatabase

    db = TahrirDatabase('backend://badges:badgesareawesome@localhost/badges')

    badge_id = 'fossbox'
    person_email = 'person@email.com'
    person_id = hash(person_email)
    issued_on = None

    db.add_person(person_id, person_email)
    db.add_assertion(badge_id, person_email, issued_on)
