# Helpers for function specific tests can be made here to reduce
# congestion in main test file.


def dummy_badges_for_search_string(api, dummy_issuer_id):
    """Seed with database with dummy badges"""
    api.add_badge(
        "TestBadge-1 rabbit",
        "TestImage-2",
        "A test badge for doing 10 unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags="tag1",
    )

    api.add_badge(
        "TestBadge-2 panda",
        "TestImage-2",
        "A test badge for doing 200 unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags="tag4",
    )

    api.add_badge(
        "TestBadge-3 rabbit panda",
        "TestImage-4",
        "A test badge for doing 60 unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags="tag2",
    )

    api.add_badge(
        "TestBadge-4 deer",
        "TestImage-2",
        "A test badge for doing 400 unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags="tag1, tag4",
    )
    api.add_badge(
        "TestBadge-5 rabbit",
        "TestImage-3",
        "A test badge for doing 50 unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags="tag3",
    )

    api.add_badge(
        "TestBadge-6 deer",
        "TestImage-5",
        "A test badge for doing 600 unit tests",
        "TestCriteria",
        dummy_issuer_id,
        tags="tag2, tag4",
    )

    return True


def dummy_persons_for_search_string(api):
    data = [
        {"nickname": "John", "email": "test1@tester.com"},
        {"nickname": "Joshua", "email": "test2@tester.com"},
        {"nickname": "Jane", "email": "test3@tester.com"},
        {"nickname": "Bane", "email": "test4@tester.com"},
        {"nickname": "pear", "email": "test5@tester.com"},
        {"nickname": "t0xic", "email": "test6@tester.com"},
    ]

    for person in range(0, 6):
        api.add_person(data[person]["email"], data[person]["nickname"])
    return True
