from appsec_discovery.parsers import ParserFactory
from appsec_discovery.parsers.protobuf.parser import ProtobufParser
import os
from pathlib import Path

def test_parser_protobuf_get_parser():

    pf = ParserFactory()

    parser = pf.get_parser('protobuf')
    assert parser.__qualname__ == "ProtobufParser"


def test_parser_protobuf_parse_folder():

    pf = ParserFactory()

    parserCls = pf.get_parser('protobuf')

    test_folder = str(Path(__file__).resolve().parent)
    samples_folder = os.path.join(test_folder, "protobuf_samples")

    pr: ProtobufParser = parserCls(parser='protobuf', source_folder=samples_folder)

    results = pr.run_scan()

    assert len(results) == 7

    assert 'Rpc' in results[5].object_name

    assert len(results[6].fields) > 0 
