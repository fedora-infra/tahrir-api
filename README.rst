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

Development
===========

System Requirements
-------------------

Before getting started, ensure your system meets the following requirements:

**Software Requirements**

- **Python**: 3.9 or higher 
- **uv**: Latest version for dependency management
- **Database**: PostgreSQL 9.6+ (recommended) or SQLite (basic development)
- **Git**: For version control

**Operating System Requirement**

- **Fedora Linux**: Latest non-EOL versions

Note: Other distributions may work, but are not officially supported. The maintainers may not be able to assist with platform-specific issues on non-Fedora systems.

Project Setup
-------------
1. Ensure that the necessary packages are installed:

.. code-block:: bash

    $ sudo dnf install -y python3 python3-pip python3-devel uv gcc krb5-devel git

2. Clone your fork to the local storage and make it your current working directory:

.. code-block:: bash

    $ git clone https://github.com/fedora-infra/tahrir-api.git
    $ cd tahrir-api

3. Create a virtual environment and activate it for installing project dependencies:

.. code-block:: bash

    $ python3 -m venv venv
    $ source venv/bin/activate

4. Install project dependencies:

.. code-block:: bash

    (venv) $ uv check
    (venv) $ uv install


Database Setup
--------------

1. Create a directory for storing the Tahrir database snapshot:

.. code-block:: bash

    (venv) $ cd ..
    (venv) $ mkdir badges-database
    (venv) $ cd badges-database

2. Download and extract the Tahrir database snapshot:

.. code-block:: bash

    (venv) $ wget https://infrastructure.fedoraproject.org/infra/db-dumps/tahrir.dump.xz
    (venv) $ unxz tahrir.dump.xz

3. Create directories for persistent data and the database dump:

.. code-block:: bash

    (venv) $ mkdir data dump
    (venv) $ mv tahrir.dump dump/

4. Pull the PostgreSQL container image:

.. code-block:: bash

    (venv) $ podman pull docker.io/library/postgres:15

5. Start the database container (be sure to rename the username and paths based on your development environment):

.. code-block:: bash

    (venv) $ podman run \
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

6. Once the database container has started, log in to the interactive shell using the password to begin importing the extracted dump:

.. code-block:: bash

   (venv )$ podman pull docker.io/library/postgres:15
   (venv )$ podman run \

7. Execute the following SQL commands to create roles, load the database dump, and grant the needed access:

.. code-block:: sql

    badgesdb=# create role "tahrir" with inherit nocreatedb nocreaterole noreplication nosuperuser valid until 'infinity' login password 'tahrir';
    badgesdb=# create role "tahrir-readonly" with nocreatedb inherit nocreaterole noreplication nosuperuser valid until 'infinity' login password 'tahrir-readonly';
    badgesdb=# \i badgesdb/tahrir.dump
    badgesdb=# grant connect on database tahrir to "tahrir";
    badgesdb=# grant all on all tables in schema public to "tahrir";
    badgesdb=# grant all on all sequences in schema public to "tahrir";
    badgesdb=# revoke create on schema public from public;

8. Exit out of the interactive shell and log back in using the newly created credentials:

.. code-block:: bash

     (venv )$ podman exec -ti badges-database psql --username badgesdb --password

9. Verify the database setup:

.. code-block:: sql

    (venv )$ tahrir=> \dt+

Run the tests
-------------

1. Download and install ``tox``:

.. code-block:: bash

    (venv) $ cd ./tahrir-api
    (venv) $ sudo dnf install tox

2. Run the tests with ``tox``:

.. code-block:: bash

    (venv) $ tox


