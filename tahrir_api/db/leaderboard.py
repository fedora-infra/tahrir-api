from collections import OrderedDict
from datetime import datetime, timezone

from sqlalchemy import func, not_, select, text
from tahrir_messages import PersonRankAdvanceV1

from ..model import Assertion, CurrentValue, Person
from ..utils import autocommit


class LeaderboardMethod:
    """leaderboard, rank, and current-value operations."""

    def get_current_value(self, badge_id: str, person_email: str) -> int | None:
        """
        Return the current value for the given badge and the given person's email

        :type badge_id: str
        :param badge_id: The ID of the badge to query
        :type person_email: str
        :param person_email: The email of the person to query
        """
        if not self.badge_exists(badge_id):
            raise ValueError(f"No such badge {badge_id!r}")

        person = self.get_person(person_email=person_email)
        if person is None:
            return None

        query = select(CurrentValue.value).where(
            CurrentValue.badge_id == badge_id,
            CurrentValue.person_id == person.id,
        )
        return self.session.scalar(query)

    @autocommit
    def set_current_value(self, badge_id: str, person_email: str, value: int) -> None:
        """Set the current value for the given badge and the given person's email

        :type badge_id: str
        :param badge_id: The ID of the badge to query
        :type person_email: str
        :param person_email: The email of the person to query
        :type value: int
        :param value: The value to store
        """
        if not self.badge_exists(badge_id):
            raise ValueError(f"No such badge {badge_id!r}")

        person = self.get_person(person_email=person_email)
        if person is None:
            self.add_person(email=person_email)
            person = self.get_person(person_email=person_email)

        now = datetime.now(tz=timezone.utc)
        query = select(CurrentValue).where(
            CurrentValue.badge_id == badge_id,
            CurrentValue.person_id == person.id,
        )
        current_value = self.session.scalar(query)
        if current_value is None:
            current_value = CurrentValue(badge_id=badge_id, value=value, last_update=now)
            person.current_values.append(current_value)
            self.session.flush()
        else:
            current_value.value = value
            current_value.last_update = now

    @autocommit
    def adjust_ranks(self, person: Person) -> None:
        """Given a person model object, adjust the ranks of all persons between the 'old' rank and
        the present rank of the given person.

        This is a utility function typically called when a person is awarded a
        new badge, and their rank advances.  Since we cache rank in the
        database, we want to also decrement the rank of all persons that the
        given person is "passing" on the all-time leaderboard.
        """

        old_rank = person.rank

        # Build a dict of Persons to some freshly calculated rank info.
        leaderboard = self.make_leaderboard()

        # Recalculate rank in all cases, otherwise "overtaking" won't work
        # anymore (with rank being shared, a new badge won't change a person's
        # own position but needs to demote the rest).

        # Otherwise, take our calculations and commit them to the db.
        for _person, data in leaderboard.items():
            _person.rank = data["rank"]

        self.session.flush()

        body = dict(person=person.as_dict(), old_rank=old_rank)
        if self.notification_callback:
            self.notification_callback(PersonRankAdvanceV1(body=body))

    def make_leaderboard(
        self, start: datetime | None = None, stop: datetime | None = None
    ) -> OrderedDict[Person, dict[str, int]]:
        """Produce a dict mapping persons to information about
        the number of badges they have been awarded and their
        rank, freshly calculated.  This is relatively expensive.

        The 'start' and 'stop' parameters are optional datetime objects.
        If specified, the leaderboard will be calculated from badges that were
        awarded only in the time period between 'start' and 'stop'.  Passing
        only one of 'start' or 'stop' is meaningless -- the other value will be
        discarded.  Passing neither value will return the "all time"
        leaderboard.

        People with no badges in the specified period are expected to have a
        null/None rank.  They will be absent from the returned leaderboard
        dict.

        Ricky Elrod originally contributed this to tahrir.
        Moved here by Ralph Bean.
        """

        leaderboard = self.session.query(
            Person, func.count(Person.assertions).label("count_1")
        ).join(Assertion)

        if start and stop:
            leaderboard = leaderboard.filter(Assertion.issued_on >= start).filter(
                Assertion.issued_on <= stop
            )

        leaderboard = (
            leaderboard.order_by(text("count_1 desc"))
            .filter(not_(Person.opt_out))
            .group_by(Person)
            .all()
        )

        # Hackishly, but relatively cheaply get the rank of all users.
        # This is:
        # { <person object>:
        #   {
        #     'badges': <number of badges they have>,
        #     'rank': <their global rank>
        #   }
        # }
        #
        # Tweaked so that users with the same amount of badges share rank.

        user_to_rank: OrderedDict[Person, dict[str, int]] = OrderedDict()

        prev_rank, prev_badges = None, None

        for idx, data in enumerate(leaderboard):
            user, badges = data[0:2]
            if badges == prev_badges:
                # same amount of badges -> same rank
                rank = prev_rank
            else:
                prev_rank = rank = idx + 1
                prev_badges = badges
            user_to_rank[user] = {"badges": badges, "rank": rank}

        return user_to_rank
