import appsec_discovery

def test_sample():
    assert appsec_discovery.some_function(name="expected_result") == "expected_result"
    assert appsec_discovery.some_function() == "world"
