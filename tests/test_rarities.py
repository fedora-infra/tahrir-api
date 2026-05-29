import pytest

from tahrir_api.model import Rarity


@pytest.fixture
def dummy_persons(api):
    """Create 12 persons so bucket maths work cleanly with 12 badges."""
    for i in range(12):
        api.add_person(f"person{i}@test.com")


@pytest.fixture
def dummy_badges_with_assertions(api, dummy_issuer_id, dummy_persons):
    """
    Create 12 badges with descending assertion counts:
    badge_0 → 12 assertions (most owned → D tier)
    badge_11 → 1 assertion  (least owned → X tier)
    """
    for i in range(12):
        badge_id = api.add_badge(
            f"RarityBadge_{i}",
            f"RarityImage_{i}",
            f"RarityDesc_{i}",
            f"RarityCrit_{i}",
            dummy_issuer_id,
        )
        for j in range(12 - i):
            api.add_assertion(badge_id, f"person{j}@test.com", None, f"link_{i}_{j}")


def test_compute_badge_rarities_standard_case(api, dummy_badges_with_assertions):
    """12 badges / 6 tiers: names, assignment, distribution, limits, X and D placement."""
    api.compute_badge_rarities()

    rarities = api.session.query(Rarity).all()
    badges = api.get_all_badges().all()
    rarity_by_name = {r.name: r for r in rarities}

    assert len(rarities) == 6
    assert set(rarity_by_name) == {"X", "S", "A", "B", "C", "D"}
    assert all(badge.rarity_id is not None for badge in badges)

    for rarity in rarities:
        count = sum(1 for b in badges if b.rarity_id == rarity.id)
        assert count == 2
        assert rarity.lower_limit >= 0.0
        assert rarity.upper_limit >= rarity.lower_limit

    x_tier = rarity_by_name["X"]
    d_tier = rarity_by_name["D"]
    x_badges = [b for b in badges if b.rarity_id == x_tier.id]
    d_badges = [b for b in badges if b.rarity_id == d_tier.id]
    assert any("RarityBadge_11" in b.name for b in x_badges)
    assert any("RarityBadge_0" in b.name for b in d_badges)


def test_compute_badge_rarities_no_users_returns_early(api, dummy_issuer_id):
    """With no users in the DB, compute should return without error."""
    api.add_badge("EmptyBadge", "img", "desc", "crit", dummy_issuer_id)
    api.compute_badge_rarities()  # should not raise
    badges = api.get_all_badges().all()
    assert all(badge.rarity_id is None for badge in badges)


def test_compute_badge_rarities_idempotent(api, dummy_badges_with_assertions):
    """Calling compute twice should update existing rows, not crash on unique constraints."""
    api.compute_badge_rarities()
    first_run = {r.name: (r.lower_limit, r.upper_limit) for r in api.session.query(Rarity).all()}

    api.compute_badge_rarities()
    second_run = {r.name: (r.lower_limit, r.upper_limit) for r in api.session.query(Rarity).all()}

    assert api.session.query(Rarity).count() == 6
    assert first_run == second_run


def test_compute_badge_rarities_fewer_than_six_badges(api, dummy_issuer_id):
    """With 3 badges and 6 tiers, some tiers should be empty."""
    for i in range(3):
        api.add_person(f"few{i}@test.com")
    for i in range(3):
        badge_id = api.add_badge(
            f"FewBadge_{i}", f"img_{i}", f"desc_{i}", f"crit_{i}", dummy_issuer_id
        )
        for j in range(3 - i):
            api.add_assertion(badge_id, f"few{j}@test.com", None, f"link_{i}_{j}")

    api.compute_badge_rarities()
    badges = api.get_all_badges().all()
    assert all(b.rarity_id is not None for b in badges)


def test_compute_badge_rarities_uneven_badge_count(api, dummy_issuer_id):
    """7 badges / 6 tiers exercises the remainder distribution logic."""
    for i in range(7):
        api.add_person(f"uneven{i}@test.com")
    for i in range(7):
        badge_id = api.add_badge(
            f"UnevenBadge_{i}", f"img_{i}", f"desc_{i}", f"crit_{i}", dummy_issuer_id
        )
        for j in range(7 - i):
            api.add_assertion(badge_id, f"uneven{j}@test.com", None, f"link_{i}_{j}")

    api.compute_badge_rarities()
    badges = api.get_all_badges().all()
    assert all(b.rarity_id is not None for b in badges)
    tier_counts = {}
    for b in badges:
        tier_counts[b.rarity_id] = tier_counts.get(b.rarity_id, 0) + 1
    assert sum(tier_counts.values()) == 7
    # One tier gets the extra badge from remainder
    assert max(tier_counts.values()) == 2


def test_compute_badge_rarities_badge_with_zero_assertions(api, dummy_issuer_id):
    """A badge with zero assertions should still be assigned a rarity."""
    for i in range(6):
        api.add_person(f"zero{i}@test.com")
    for i in range(6):
        badge_id = api.add_badge(
            f"ZeroBadge_{i}", f"img_{i}", f"desc_{i}", f"crit_{i}", dummy_issuer_id
        )
        if i < 5:
            api.add_assertion(badge_id, f"zero{i}@test.com", None, f"link_{i}")

    api.compute_badge_rarities()
    badges = api.get_all_badges().all()
    assert all(b.rarity_id is not None for b in badges)
    # The badge with 0 assertions should be in X tier (least owned)
    zero_badge = next(b for b in badges if b.name == "ZeroBadge_5")
    x_tier = api.session.query(Rarity).filter(Rarity.name == "X").first()
    assert zero_badge.rarity_id == x_tier.id
