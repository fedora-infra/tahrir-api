from datetime import datetime, timezone

from sqlalchemy import func, not_
from tahrir_messages import PersonLoginFirstV1

from ..model import Person
from ..utils import autocommit


class PersonMethod:
    """Person CRUD and profile operations."""

    def person_exists(self, email=None, id=None, nickname=None):
        """
        Check if a Person with this email is stored in the database

        :type email: str
        :param email: An email address to search the database for

        :type id: str
        :param id: A user id to search for.

        :type nickname: str
        :param nickname: A nickname to search for.
        """

        query = self.session.query(Person)
        if email:
            return query.filter(func.lower(Person.email) == func.lower(email)).count() != 0
        elif id:
            return query.filter_by(id=id).count() != 0
        elif nickname:
            return query.filter(func.lower(Person.nickname) == func.lower(nickname)).count() != 0
        else:
            return False

    def person_opted_out(self, email=None, id=None, nickname=None):
        """Returns true if a given person has opted out of tahrir."""

        person = self.get_person(email, id, nickname)

        # If they don't exist, then they haven't opted out.
        if not person:
            return False

        # Otherwise, return whatever value they have in the DB.
        return person.opt_out

    def get_all_persons(self, include_opted_out=False):
        """
        Gets all the persons in the db.
        """

        query = self.session.query(Person)
        if not include_opted_out:
            query = query.filter(not_(Person.opt_out))
        return query

    def get_persons_by_nickname(self, search_string: str, begin: int = 0, limit: int = 100):
        """
        Search for persons by nickname with pagination.

        :type search_string: str
        :param search_string: The nickname pattern to search for.
        :type begin: int
        :param begin: Offset for pagination (default 0).
        :type limit: int
        :param limit: Max results per page, capped at 100 (default 100).
        """

        safe_limit = min(limit, 100)

        query = self.session.query(Person).filter(
            func.lower(Person.nickname).like(f"%{search_string.lower()}%")
        )

        total_count = query.count()
        paginated_results = query.offset(begin).limit(safe_limit).all()
        return {
            "users": paginated_results,
            "total": total_count,
            "begin": begin,
            "limit": safe_limit,
        }

    def get_person_email(self, person_id):
        """
        Convience function to retrieve a person email from an id.

        I am so sorry that I had to write this.
        It is easier than rewriting all of the get_person and
        person_exists methods to take ids for now.
        Eventaully, I will get around to fully refactoring
        this API.

        This was written after get_person etc., and at some point we really
        should make all these methods uniform (either get_x and
        get_x_by_email or get_x and get_x_by_id).

        :type person_id: str
        :param person_id: The email of a Person in the database.
        """

        if self.person_exists(id=person_id):
            return (
                self.session.query(Person)
                .filter(func.lower(Person.id) == func.lower(person_id))
                .one()
                .email
            )
        return None

    def get_person(self, person_email=None, id=None, nickname=None):
        """
        Convenience function to retrieve a person object from an email,
        id, or nickname.

        :type person_email: str
        :param person_email: The email address of a Person in the database

        :type id: str
        :param id: The id of a Person in the database

        :type nickname: str
        :param nickname: The nickname of a Person in the database
        """

        query = self.session.query(Person)

        if person_email and self.person_exists(email=person_email):
            return query.filter(func.lower(Person.email) == func.lower(person_email)).one()
        elif id and self.person_exists(id=id):
            return query.filter_by(id=id).one()
        elif nickname and self.person_exists(nickname=nickname):
            return query.filter(func.lower(Person.nickname) == func.lower(nickname)).one()
        else:
            return None

    @autocommit
    def delete_person(self, person_email):
        """
        Delete a person with the given email

        :type person_email: str
        :param person_email: Email of the person to delete
        """

        if self.person_exists(email=person_email):
            self.session.delete(self.get_person(person_email))
            self.session.flush()
            return person_email
        return False

    @autocommit
    def add_person(self, email, nickname=None, website=None, bio=None, avatar=None):
        """
        Add a new Person to the database

        :type email: str
        :param email: This Person's email address

        :type nickname: str
        :param nickname: This Person's nickname

        :type website: str
        :param website: This Person's website

        :type bio: str
        :param bio: This Person's bio

        :type avatar: str
        :param avatar: This Person's avatar
        """

        if not self.person_exists(email=email):
            # If no nickname is specified, just use the first bit of their
            # email as a convenient default.
            if not nickname:
                nickname = email.split("@")[0]

            new_person = Person(
                email=email, nickname=nickname, website=website, bio=bio, _avatar=avatar
            )
            self.session.add(new_person)
            self.session.flush()

            return email
        return False

    @autocommit
    def update_person(
        self,
        person_email=None,
        id=None,
        nickname=None,
        website=None,
        bio=None,
        avatar=None,
    ):
        """
        Update an existing Person's profile fields in the database

        :type person_email: str
        :param person_email: Email address of the Person to update

        :type id: int
        :param id: ID of the Person to update

        :type nickname: str
        :param nickname: Nickname of the Person to update

        :type website: str
        :param website: New website URL for this Person (optional)

        :type bio: str
        :param bio: New bio text for this Person (optional)

        :type avatar: str
        :param avatar: New avatar URL for this Person (optional)
        """

        person = self.get_person(person_email, id, nickname)
        if not person:
            return False

        # Only update fields that are provided (not None)
        if website is not None:
            person.website = website
        if bio is not None:
            person.bio = bio
        if avatar is not None:
            person._avatar = avatar

        self.session.flush()
        return person

    @autocommit
    def note_login(self, person_email=None, id=None, nickname=None):
        """Make a note that a person has logged in."""

        person = self.get_person(person_email, id, nickname)

        # If this is the first time they have ever logged in, optionally
        # publish a notification about the event.
        if not person.last_login and self.notification_callback:
            body = dict(user=dict(username=person.nickname, badges_user_id=person.id))
            self.notification_callback(PersonLoginFirstV1(body=body))

        # Finally, update the field.
        person.last_login = datetime.now(timezone.utc)
