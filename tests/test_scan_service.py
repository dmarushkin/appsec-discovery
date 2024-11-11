from appsec_discovery.services import ScanService

import os
from pathlib import Path


def test_scan_service_default_config_load():

    test_folder = str(Path(__file__).resolve().parent)

    scan_service = ScanService(source_folder="some")

    score_config = scan_service.config

    assert score_config.object_types[0] == 'all'

    assert score_config.score_tags['pii']['high'][0] == 'full_name'

def test_scan_service_custom_config_load():

    test_folder = str(Path(__file__).resolve().parent)
    config_file = os.path.join(test_folder, "config_samples/conf.yaml")

    with open(config_file, 'r') as conf_file:
        scan_service = ScanService(source_folder="some", conf_file=conf_file)

    score_config = scan_service.config

    assert score_config.object_types[0] == 'all'
    
    assert score_config.score_tags['pii']['high'][0] == 'firstname'

def test_scan_service_run_scanners():

    test_folder = str(Path(__file__).resolve().parent)
    samples_folder = os.path.join(test_folder, "swagger_samples")
    only_scored_objects = False

    scan_service = ScanService(source_folder=samples_folder, only_scored_objects=only_scored_objects)

    scanned_objects = scan_service.scan_folder()
   
    # 1st scored

    assert scanned_objects[0].severity is None 

    assert scanned_objects[1].severity is not None 

    assert scanned_objects[1].severity == 'high'

    assert scanned_objects[1].properties['path'].prop_value == '/user'

    assert 'auth' in scanned_objects[1].tags

    assert not scanned_objects[1].fields['Input.User.TShortSize'].severity

    assert scanned_objects[1].fields['Input.User.email'].severity == 'medium'

