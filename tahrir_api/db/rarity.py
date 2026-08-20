from sqlalchemy import func

from ..model import Assertion, Badge, Person, Rarity
from ..utils import autocommit


class RarityMethod:
    """Rarity operations."""

    @autocommit
    def compute_badge_rarities(self) -> None:
        """
        Compute and store the rarity of all badges using equal-pile ranking.

        Legacy badges are pulled out first and assigned to the "O" (obsolete)
        tier.  The remaining active badges are sorted by assertion count
        (ascending), divided into equal pile_list of size len(badges) // 6, with
        remainder distributed from X onwards.  The lower_limit and upper_limit
        of each rarity tier are updated to reflect the ownership rate_list of
        badges in that pile.
        """

        RARITIES = ["O", "X", "S", "A", "B", "C", "D"]

        badges_full = self.session.query(Badge).all()
        if not badges_full:
            return

        rarity_dict = {r.name: r for r in self.session.query(Rarity).all()}
        for name in RARITIES:
            if name not in rarity_dict:
                rarity_dict[name] = Rarity(name=name, lower_limit=0, upper_limit=0)
                self.session.add(rarity_dict[name])
        self.session.flush()

        legacy_badges = [item for item in badges_full if item.legacy]
        active_badges = [item for item in badges_full if not item.legacy]

        for item in legacy_badges:
            item.rarity_id = rarity_dict["O"].id

        if not active_badges:
            return

        # single query for all assertion counts — avoids n+1
        counts = (
            self.session.query(
                Assertion.badge_id,
                func.count(Assertion.id).label("count"),
            )
            .group_by(Assertion.badge_id)
            .all()
        )
        counts_dict = {row.badge_id: row.count for row in counts}

        user_poll = self.session.query(Person).count()
        item_dict = {b.id: b for b in active_badges}

        if user_poll == 0 or not counts_dict:
            for item in active_badges:
                item.rarity_id = rarity_dict["D"].id
            return

        accodict = {}
        for item in active_badges:
            poll = counts_dict.get(item.id, 0)
            accodict[item.id] = {
                "poll": poll,
                "rate": poll / user_poll * 100,
            }

        # sort ascending by assertion count — least owned first → gets X
        tier_list = RARITIES[1:]
        sort_list = sorted(accodict.items(), key=lambda item: item[1]["poll"])
        size = len(sort_list) // len(tier_list)
        left = len(sort_list) % len(tier_list)
        jump = 0

        pile_list = []
        for i, rare_name in enumerate(tier_list):
            stop = jump + size + (1 if i < left else 0)
            pile = sort_list[jump:stop]

            if not pile:
                jump = stop
                continue

            rate_list = [data["rate"] for _, data in pile]
            rare_item = rarity_dict[rare_name]
            rare_item.lower_limit = min(rate_list)
            rare_item.upper_limit = max(rate_list)

            pile_list.append((rare_item, pile))
            jump = stop

        self.session.flush()

        for rare_item, pile in pile_list:
            for badge_id, _data in pile:
                item_dict[badge_id].rarity_id = rare_item.id

        self.session.flush()
