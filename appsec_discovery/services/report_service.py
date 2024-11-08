from typing import List, Dict
import logging
import yaml
import json
import sarif_om as om
from jschema_to_python.to_json import to_json

from appsec_discovery.models import CodeObject

logger = logging.getLogger(__name__)


class ReportService:

    def __init__(self, code_objects: List[CodeObject], report_type, report_file):

        self.report_type = report_type
        self.report_file = report_file

        self.code_objects = code_objects


    def save_report_to_disk(self):

        if self.report_type == 'yaml':
            report_str = self.get_yaml_report()

        if self.report_type == 'json':
            report_str = self.get_json_report()

        if self.report_type == 'sarif':
            report_str = self.get_sarif_report()

        if self.report_file :

            self.report_file.write(report_str)
            self.report_file.close()

        else:
            print(report_str)


    def get_json_report(self):

        dumped_objects = []

        for object in self.code_objects:
            dumped_objects.append(object.dict(exclude_none=True))
            
        return json.dumps(dumped_objects, indent=4)
    
    def get_yaml_report(self):

        dumped_objects = []

        for object in self.code_objects:
            dumped_objects.append(object.dict(exclude_none=True))
            
        return yaml.dump(dumped_objects, default_flow_style=False, sort_keys=False)


    def get_sarif_report(self):

        report = om.SarifLog(
            schema_uri="https://json.schemastore.org/sarif-2.1.0.json",
            version="2.1.0",
            runs=[
                om.Run(
                    tool=om.Tool(
                        driver=om.ToolComponent(
                            name="appsec-discovery",
                            semantic_version="0.1.0",
                            information_uri="https://github.com/dmarushkin/appsec-discovery",
                            rules=[]
                        )
                    ),
                    results=[]
                )
            ]
        )

        rules: Dict[str, om.ReportingDescriptor] = {}

        for object in self.code_objects:

            rule = om.ReportingDescriptor(
                id=f"{object.parser}.{object.object_type}",
                short_description={
                    "text": f"Discovered object {object.parser}.{object.object_type}"
                },
                full_description={
                    "text": f"Discovered object {object.parser}.{object.object_type}"
                },
                help={
                    "text": f"Discovered object {object.parser}.{object.object_type}"
                },
                properties={},
                default_configuration={},
            )

            rules[f"{object.parser}.{object.object_type}"] = rule

        report.runs[0].tool.driver.rules = [rule for rule in rules.values()]

        for object in self.code_objects:

            object_snippet = yaml.safe_dump(object.dict(exclude_none=True), sort_keys=False)

            region = om.Region(
                start_line=object.line,
            )
            context_region=om.Region(
                start_line=object.line,
                snippet=om.ArtifactContent(text=object_snippet)
            )

            level = 'note'
            properties = {}
            severity = 'info'

            if object.severity and object.severity in ['critical','high']:
                level = 'error'
                severity = object.severity
            
            if object.severity and object.severity in ['medium','low']:
                level = 'warning'
                severity = object.severity

            if object.severity and object.tags :
                properties = {"tags": object.tags }

            result = om.Result(
                rule_id=f"{object.parser}.{object.object_type}",
                level=level,
                properties=properties,
                message=om.Message(
                    text=f"[{object.parser}.{object.object_type}] {object.object_name}"
                ),
                locations=[
                    om.Location(
                        physical_location=om.PhysicalLocation(
                            artifact_location=om.ArtifactLocation(
                                uri=object.file,
                                uri_base_id="%SRCROOT%"
                            ),
                            region=region,
                            context_region=context_region
                        )
                    )
                ]
            )

            report.runs[0].results.append(result)

        return to_json(report)

    