import logging
import os
import copy
from typing import List, Dict
from pathlib import Path

from appsec_discovery.parsers import Parser
from appsec_discovery.models import CodeObject, CodeObjectProp, CodeObjectField

logger = logging.getLogger(__name__)

class SwaggerParser(Parser):

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

        objects_dict = {}
        routes_dict = {}

        for finding in semgrep_data:

            finding_file = finding.get('path')
            finding_line_int = finding.get('start',{}).get('line',0)

            rule_id = finding.get('check_id',"").split('.')[-1]

            if rule_id == 'swagger-schema':

                object = finding.get('extra').get('metavars').get('$OBJECT', {}).get('abstract_content',"")
                field_name = finding.get('extra').get('metavars').get('$FIELD', {}).get('abstract_content',"")
                field_type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"")
                field_ref = finding.get('extra').get('metavars').get('$REF', {}).get('abstract_content',"").split('/')[-1]

                if object not in objects_dict:
                    objects_dict[object] = {}
                
                if field_name not in objects_dict[object]:
                    objects_dict[object][field_name] = {'field_type': field_type, 'ref': field_ref}

                if field_ref and objects_dict[object][field_name]['field_type'] != 'ref':
                    objects_dict[object][field_name]['field_type'] = 'ref'
                    objects_dict[object][field_name]['ref'] = field_ref

        # resolving refs

        no_changes = False
        while not no_changes:

            no_changes = True
            objects_dict_copy = copy.deepcopy(objects_dict)

            for obj, obj_fields in objects_dict_copy.items():
                for field, field_data in obj_fields.items():

                    if field_data['ref'] in objects_dict_copy:

                        for ref_field, ref_field_data in objects_dict_copy[field_data['ref']].items():
                            objects_dict[obj][f"{field}.{ref_field}"] = ref_field_data

                        del objects_dict[obj][field]
                        no_changes = False

        for finding in semgrep_data:

            finding_file = finding.get('path')
            finding_line_int = finding.get('start',{}).get('line',0)

            rule_id = finding.get('check_id',"").split('.')[-1]

            if rule_id != 'swagger-schema':

                path = finding.get('extra').get('metavars').get('$PATH', {}).get('abstract_content',"").strip('"').strip("'")
                method = finding.get('extra').get('metavars').get('$METHOD', {}).get('abstract_content',"").strip('"').strip("'")

                field_name = finding.get('extra').get('metavars').get('$PARAM', {}).get('abstract_content',"").strip('"').strip("'")
                field_type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"").strip('"').strip("'")

                req_ref = finding.get('extra').get('metavars').get('$REQREF', {}).get('abstract_content',"").split('/')[-1]
                resp_ref = finding.get('extra').get('metavars').get('$RESPREF', {}).get('abstract_content',"").split('/')[-1]

                hash_key = self.calc_uniq_hash([finding_file, path, method])
                field_hash_key = self.calc_uniq_hash([finding_file, path, method, field_name])
                req_ref_hash_key = self.calc_uniq_hash([finding_file, path, method, req_ref, 'req'])
                resp_ref_hash_key = self.calc_uniq_hash([finding_file, path, method, resp_ref, 'resp'])

                object_name = f"Swagger route {path} ({method.upper()})"

                if hash_key not in parsed_objects_dict:

                    parsed_objects_dict[hash_key] = CodeObject(
                        hash=hash_key,
                        object_name=object_name,
                        object_type="route",
                        parser=self.parser,
                        file=finding_file,
                        line=finding_line_int,
                        properties={},
                        fields={}
                    )

                    parsed_objects_dict[hash_key].properties['path'] = CodeObjectProp(
                        prop_name='path',
                        prop_value=path
                    )

                    parsed_objects_dict[hash_key].properties['method'] = CodeObjectProp(
                        prop_name='method',
                        prop_value=method
                    )

                if field_name and field_hash_key not in parsed_fields_dict:

                    parsed_field = CodeObjectField(
                        field_name=f"Input.{field_name}",
                        field_type=field_type,
                        file=finding_file,
                        line=finding_line_int
                    )

                    parsed_objects_dict[hash_key].fields[parsed_field.field_name] = parsed_field
                    parsed_fields_dict[field_hash_key] = parsed_field

                if req_ref in objects_dict and req_ref_hash_key not in parsed_fields_dict:
                    for ref_field, ref_field_data in objects_dict[req_ref].items():

                        parsed_field = CodeObjectField(
                            field_name=f"Input.{req_ref}.{ref_field}",
                            field_type=ref_field_data['field_type'],
                            file=finding_file,
                            line=finding_line_int
                        )

                        parsed_objects_dict[hash_key].fields[parsed_field.field_name] = parsed_field
                        parsed_fields_dict[req_ref_hash_key] = parsed_field

                if resp_ref in objects_dict and resp_ref_hash_key not in parsed_fields_dict:
                    for ref_field, ref_field_data in objects_dict[resp_ref].items():

                        parsed_field = CodeObjectField(
                            field_name=f"Output.{resp_ref}.{ref_field}",
                            field_type=ref_field_data['field_type'],
                            file=finding_file,
                            line=finding_line_int
                        )

                        parsed_objects_dict[hash_key].fields[parsed_field.field_name] = parsed_field
                        parsed_fields_dict[resp_ref_hash_key] = parsed_field

        if parsed_objects_dict:
            parsed_objects = list(parsed_objects_dict.values())

        logger.info(f"For scan {self.parser} data parse {len(parsed_objects)} objects")
        return parsed_objects