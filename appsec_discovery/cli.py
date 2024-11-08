import click

from appsec_discovery.services import ScanService, ReportService

@click.command()
@click.option('--source', required=True, type=click.Path(exists=True), help='Source code folder')
@click.option('--config', required=False, show_default=True, default=None, type=click.File('r'), help='Scoring config file')
@click.option('--output', required=False, show_default=True, default=None, type=click.File('w'), help='Output file')
@click.option('--output-type', required=False, show_default=True, default='yaml', type=click.Choice(['json', 'sarif', 'yaml'], case_sensitive=False), help='Report type')
@click.option("--only-scored-objects", is_flag=True, show_default=True, default=False, help="Show only scored objects")
def main(source, config, output, output_type, only_scored_objects):

    scan_service = ScanService(source_folder=source, conf_file=config, only_scored_objects=only_scored_objects)
    scanned_objects = scan_service.scan_folder()

    report_service = ReportService(code_objects=scanned_objects, report_type=output_type, report_file=output)
    report_service.save_report_to_disk()

if __name__ == '__main__':
    main()
