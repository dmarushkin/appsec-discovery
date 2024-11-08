from appsec_discovery.parsers import ParserFactory
from appsec_discovery.parsers.terraform.parser import TerraformParser
import os
from pathlib import Path

def test_parser_terraform_get_parser():

    pf = ParserFactory()

    parser = pf.get_parser('terraform')
    assert parser.__qualname__ == "TerraformParser"


def test_parser_terraform_parse_folder():

    pf = ParserFactory()

    parserCls = pf.get_parser('terraform')

    test_folder = str(Path(__file__).resolve().parent)
    samples_folder = os.path.join(test_folder, "terraform_samples")

    pr: TerraformParser = parserCls(parser='terraform', source_folder=samples_folder)

    results = pr.run_scan()

    assert len(results) == 3 

    assert results[0].parser == 'terraform'

    assert results[0].object_name == 'Virtual machine keycloak01-dc1.v.pci-prod.example.local'

    assert results[0].properties['vm_template'].prop_value == 'ubuntu-2204'

    assert results[-1].properties['vm_domain'].prop_value == 'v.pci-prod.example.local'