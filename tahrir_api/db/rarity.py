from sqlalchemy import func

from ..model import Assertion, Badge, Person, Rarity
from ..utils import autocommit


class RarityMethod:
    """Rarity operations."""

    @autocommit
    def compute_badge_rarities(self):
        """
        Compute and store the rarity of all badges using equal-pile ranking.

        Badges are sorted by assertion count (ascending), divided into equal
        piles of size len(badges) // 6, with remainder distributed from X
        onwards. The lower_limit and upper_limit of each rarity tier are
        updated to reflect the ownership rates of badges in that pile.
        """

        RARITIES = ["X", "S", "A", "B", "C", "D"]

        # single query for all assertion counts — avoids n+1
        counts = (
            self.session.query(
                Assertion.badge_id,
                func.count(Assertion.id).label("count"),
            )
            .group_by(Assertion.badge_id)
            .all()
        )

        userpoll = self.session.query(Person).count()

        if userpoll == 0:
            return

        # build the same accodict structure as the frontend script
        accodict = {}
        count_map = {row.badge_id: row.count for row in counts}

        all_badges = self.session.query(Badge).all()
        item_dict = {b.id: b for b in all_badges}
        for badge in all_badges:
            poll = count_map.get(badge.id, 0)
            accodict[badge.id] = {
                "poll": poll,
                "rate": poll / userpoll * 100,
            }

        # sort ascending by assertion count — least owned first → gets X
        sorted_items = sorted(accodict.items(), key=lambda item: item[1]["poll"])
        size = len(sorted_items) // len(RARITIES)
        left = len(sorted_items) % len(RARITIES)
        jump = 0

        piles = []
        for i, rare_name in enumerate(RARITIES):
            stop = jump + size + (1 if i < left else 0)
            pile = sorted_items[jump:stop]

            if not pile:
                jump = stop
                continue

            # compute tier boundaries from ownership rates in this pile
            rates = [data["rate"] for _, data in pile]
            lower = min(rates)
            upper = max(rates)

            # update the rarities table row for this tier
            rarity_row = self.session.query(Rarity).filter(Rarity.name == rare_name).first()
            if rarity_row:
                rarity_row.lower_limit = lower
                rarity_row.upper_limit = upper
            else:
                rarity_row = Rarity(name=rare_name, lower_limit=lower, upper_limit=upper)
                self.session.add(rarity_row)

            piles.append((rarity_row, pile))
            jump = stop

        self.session.flush()

        # assign rarity to each badge in its pile
        for rarity_row, pile in piles:
            for badge_id, _data in pile:
                item_dict[badge_id].rarity_id = rarity_row.id

        self.session.flush()
