from appsec_discovery.services import ScanService, ReportService

import yaml
import os
from pathlib import Path


def test_report_service_save_json():

    test_folder = str(Path(__file__).resolve().parent)
    config_file = os.path.join(test_folder, "config_samples/conf.yaml")
    samples_folder = os.path.join(test_folder, "terraform_samples")
    report_file = os.path.join(test_folder, "report_samples/report.json")

    with open(config_file, 'r') as conf_file:
        scan_service = ScanService(source_folder=samples_folder, conf_file=conf_file)

    scanned_objects = scan_service.scan_folder()

    with open(report_file, 'w') as report_file:

        report_service = ReportService(
            code_objects=scanned_objects,
            report_type='json',
            report_file=report_file
        )

        report_str = report_service.get_json_report()

        report_service.save_report_to_disk()

    assert "object_name" in report_str 


def test_report_service_save_sarif():

    test_folder = str(Path(__file__).resolve().parent)
    config_file = os.path.join(test_folder, "config_samples/conf.yaml")
    samples_folder = os.path.join(test_folder, "terraform_samples")
    report_file = os.path.join(test_folder, "report_samples/report.sarif")

    with open(config_file, 'r') as conf_file:
        scan_service = ScanService(source_folder=samples_folder, conf_file=conf_file)

    scanned_objects = scan_service.scan_folder()

    with open(report_file, 'w') as report_file:

        report_service = ReportService(
            code_objects=scanned_objects,
            report_type='sarif',
            report_file=report_file
        )

        report_str = report_service.get_sarif_report()

        report_service.save_report_to_disk()

    assert "json.schemastore.org" in report_str 