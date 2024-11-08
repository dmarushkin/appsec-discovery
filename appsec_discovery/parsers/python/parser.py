import logging
import os
from typing import List, Dict
from pathlib import Path

from appsec_discovery.parsers import Parser
from appsec_discovery.models import CodeObject, CodeObjectField, CodeObjectProp

logger = logging.getLogger(__name__)

class PythonParser(Parser):

    def run_scan(self) -> List[CodeObject]:

        objects_list: List[CodeObject] = []

        parser_folder = str(Path(__file__).resolve().parent)

        rules_folder = os.path.join(parser_folder, "scanner_rules")

        if os.path.isdir(rules_folder):
            
            semgrep_data = self.run_semgrep(source_folder=self.source_folder, rules_folder=rules_folder)
            objects_list = self.parse_report(semgrep_data)
        
        return objects_list


    def parse_report(self, semgrep_data) -> List[CodeObject]:

        parsed_objects: List[CodeObject] = []
        parsed_objects_dict: Dict[str, CodeObject] = {}
        parsed_fields_dict = {}

        for finding in semgrep_data:

            finding_file = finding.get('path')
            finding_line_int = finding.get('start',{}).get('line',0)

            rule_id = finding.get('check_id',"").split('.')[-1]

            object_type = None

            # parse dto rules
            if rule_id.startswith("dto-"):

                object_type="dto"
                orm_type = rule_id.split('-')[1]

                object = finding.get('extra').get('metavars').get('$OBJECT', {}).get('abstract_content',"")
                field_name = finding.get('extra').get('metavars').get('$FIELD', {}).get('abstract_content',"")
                field_type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"")

                hash_key = self.calc_uniq_hash([finding_file, object])
                field_hash_key = self.calc_uniq_hash([finding_file, object, field_name])

                if hash_key not in parsed_objects_dict:

                    parsed_objects_dict[hash_key] = CodeObject(
                        hash=hash_key,
                        object_name=f"{orm_type.title()} {object_type} {object}",
                        object_type=object_type,
                        parser=self.parser,
                        file=finding_file,
                        line=finding_line_int,
                        properties={},
                        fields=[]
                    )

                    parsed_objects_dict[hash_key].properties['framework'] = CodeObjectProp(
                        prop_name='framework',
                        prop_value=orm_type
                    )

                    parsed_objects_dict[hash_key].properties['object'] = CodeObjectProp(
                        prop_name='object',
                        prop_value=object
                    )

                if field_hash_key not in parsed_fields_dict:

                    parsed_field = CodeObjectField(
                        field_name=field_name,
                        field_type=field_type,
                        file=finding_file,
                        line=finding_line_int
                    )

                    parsed_objects_dict[hash_key].fields[parsed_field.field_name] = parsed_field

                    parsed_fields_dict[field_hash_key] = parsed_field

            # parse route rules
            if rule_id.startswith("route-"):

                object_type="route"

                fw_type = rule_id.split('-')[1].title()

                route_path = finding.get('extra').get('metavars').get('$PATH', {}).get('abstract_content',"").strip('"').strip("'")            
                route_func = finding.get('extra').get('metavars').get('$FUNC', {}).get('abstract_content',"").strip('"').strip("'")
                route_method = finding.get('extra').get('metavars').get('$METHOD', {}).get('abstract_content',"").strip('"').strip("'")

                hash_key = self.calc_uniq_hash([finding_file, route_path, route_func])

                if route_method:
                    object_name = f"{fw_type} route {route_path} calls {route_func.title()} handler ({route_method.upper()})"
                else:
                    object_name = f"{fw_type} route {route_path} calls {route_func.title()} handler"

                if hash_key not in parsed_objects_dict:

                    parsed_objects_dict[hash_key] = CodeObject(
                        hash=hash_key,
                        object_name=object_name,
                        object_type=object_type,
                        parser=self.parser,
                        file=finding_file,
                        line=finding_line_int,
                        properties={},
                        fields={}
                    )

                    parsed_objects_dict[hash_key].properties['framework'] = CodeObjectProp(
                        prop_name='framework',
                        prop_value=fw_type
                    )

                    parsed_objects_dict[hash_key].properties['func'] = CodeObjectProp(
                        prop_name='func',
                        prop_value=route_func
                    )

                    parsed_objects_dict[hash_key].properties['path'] = CodeObjectProp(
                        prop_name='path',
                        prop_value=route_path
                    )

                    if route_method :

                        parsed_objects_dict[hash_key].properties['method'] = CodeObjectProp(
                            prop_name='method',
                            prop_value=route_method
                        )
        
        if parsed_objects_dict:
            parsed_objects = list(parsed_objects_dict.values())

        logger.info(f"For scan {self.parser} data parse {len(parsed_objects)} objects")
        return parsed_objects