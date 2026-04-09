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

Pre-requisite 
-------------
-  **Python**: version 3.09 or higher.
- **Postgresql**: most recent version 15.
- Git
- Poetry 
- tox
- Fedora OS 

Cloning the Repository
----------------------
Clone the Tahrir-api repository in your local project development directory and make it the present working directory.

.. code-block:: bash
    $ git clone git@github.com:fedora-infra/tahrir-api.git

.. code-block:: bash
    $ cd tahrir-api
    


Set-up your env
---------------

Build your virtual env

.. code-block:: bash

    $ python3 -m venv tahrir-api

Connect with your virutal env

.. code-block:: bash

    $ source tahrir-api/bin/activate
    (tahrir-api)$

Set up your database
--------------------
1. Navigate back to your local project development directory and make it the present working directory.

.. code-block:: bash

    (tahrir-api)$ deactivate
    $ cd ..

2. Create a new directory.

.. code-block:: bash

    $ mkdir badges-database

.. code-block:: bash

    $ cd badges-database

3. Download the updated Tahrir database snapshot and extract its contents into the database folder.

.. code-block:: bash

    $ wget https://infrastructure.fedoraproject.org/infra/db-dumps/tahrir.dump.xz

.. code-block:: bash

    $ unxz tahrir.dump.xz

4. Create two new folders in the database folder for the ``data`` and the ``dump`` contents before moving the extracted dump over.

.. code-block:: bash

    $ mkdir data dump

.. code-block:: bash

    $ mv tahrir.dump dump/

5. Ensure you have the most recent ``postgres:15 - most recent version 15`` before configuring and using the start command.
Please be sure to rename the postgres access details, ``username`` and the paths based on how you have structured your development environment. 

.. code-block:: bash

    $ podman pull docker.io/library/postgres:15

.. code-block:: bash

    $ podman run \
        --name badges-database \
        --env POSTGRES_USER=badgesdb \
        --env POSTGRES_PASSWORD=badgesdb \
        --env POSTGRES_DB=badgesdb \
        --env PGDATA=/var/lib/postgresql/data/pgdata \
        --volume /home/username/Projects/badges-database/data:/var/lib/postgresql/data:Z \
        --volume /home/username/Projects/badges-database/dump:/badgesdb:Z \
        --publish 5432:5432 \
        --restart unless-stopped \
        --detach docker.io/library/postgres:15

6. Once the database container has started, log in to the interactive shell using the password to begin importing the extracted dump.

.. code-block:: bash

    $ podman exec -ti badges-database psql --username badgesdb --password

.. code-block:: bash

    badgesdb=# create role "tahrir" with inherit nocreatedb nocreaterole noreplication nosuperuser valid until 'infinity' login password 'tahrir';

.. code-block:: bash

    badgesdb=# create role "tahrir-readonly" with nocreatedb inherit nocreaterole noreplication nosuperuser valid until 'infinity' login password 'tahrir-readonly';

.. code-block:: bash

    badgesdb=# \i badgesdb/tahrir.dump

.. code-block:: bash

    badgesdb=# grant connect on database tahrir to "tahrir";

.. code-block:: bash

    badgesdb=# grant all on all tables in schema public to "tahrir";

.. code-block:: bash

    badgesdb=# grant all on all sequences in schema public to "tahrir";

.. code-block:: bash

    $ badgesdb=# revoke create on schema public from public;

7. Exit out of the interactive shell of the database container - only to log back in again using the newly created credentials, Then check if the data are correctly imported.

.. code-block:: bash

    $ podman exec -ti badges-database psql --username tahrir --password

.. code-block:: bash

    $ tahrir=> \dt+

8. Always ensure your PostgreSQL Container Image is active before performing any operations

.. code-block:: bash

    $ podman ps

9. **NOTE:** Your connection URI to the database would be in this format below. It would be used to make all your request to the db we just created. See the ``examples/`` directory to see how it is used.

.. code-block:: bash

    SQLALCHEMY_DATABASE_URI = "postgresql://tahrir:tahrir@<YOUR_IP_ADDR>:5432/tahrir"


Install
-------
Exit the current ``badges-database`` directory and head back into ``tahrir-api`` and start the environment

.. code-block:: bash

    $ cd ..
    $ cd tahrir-api


.. code-block:: bash

    $ source tahrir-api/bin/activate
    (tahrir-api)$

Dependencies

.. code-block:: bash

    (tahrir-api)$ poetry install

Ensure python headers are installed. These are specific to configs in ``tox.ini``

.. code-block:: bash
    
    (tahrir-api)$ sudo dnf install python3.9-devel python3.10-devel python3.11-devel python3.12-devel # On Fedora/RHEL

Run the tests
-------------

You can run the tests with ``tox``

.. code-block:: bash

    (tahrir-api)$ pip install tox
    (tahrir-api)$ tox

Happy Hacking!