def test_add_issuer(api, dummy_issuer_id):
    assert api.get_issuer(dummy_issuer_id).__str__() == "TestName"
    assert api.issuer_exists("TestOrigin", "TestName") is True
