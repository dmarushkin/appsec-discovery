from appsec_discovery.parsers import ParserFactory

def test_parser_factory_get_parser():

    pf = ParserFactory()

    parser = pf.get_parser('protobuf')
    assert parser.__qualname__ == "ProtobufParser"

    parser = pf.get_parser('graphql')
    assert parser.__qualname__ == "GraphqlParser"


def test_parser_factory_get_parser_types():

    pf = ParserFactory()

    parser_types = pf.get_parser_types()
    assert 'protobuf' in parser_types

    parser_types = pf.get_parser_types()
    assert 'graphql' in parser_types