import logging
import os
from typing import List, Dict
from pathlib import Path

from appsec_discovery.parsers import Parser
from appsec_discovery.models import CodeObject, CodeObjectProp, CodeObjectField

logger = logging.getLogger(__name__)

class JavaParser(Parser):

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

                object = finding.get('extra').get('metavars').get('$OBJECT', {}).get('abstract_content',"").strip('"').strip("'")
                db_table = finding.get('extra').get('metavars').get('$DB_NAME', {}).get('abstract_content',"").strip('"').strip("'")
                db_field = finding.get('extra').get('metavars').get('$DB_FIELD', {}).get('abstract_content',"").strip('"').strip("'")       
                field_type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"").strip('"').strip("'")

                hash_key = self.calc_uniq_hash([finding_file, object])
                field_hash_key = self.calc_uniq_hash([finding_file, object, db_field])

                if hash_key not in parsed_objects_dict:

                    parsed_objects_dict[hash_key] = CodeObject(
                        hash=hash_key,
                        object_name=f"{orm_type.title()} {object_type} {object}",
                        object_type=object_type,
                        parser=self.parser,
                        file=finding_file,
                        line=finding_line_int,
                        properties={},
                        fields={}
                    )

                    parsed_objects_dict[hash_key].properties['framework'] = CodeObjectProp(
                        prop_name='framework',
                        prop_value=orm_type
                    )

   
                    parsed_objects_dict[hash_key].properties['object'] = CodeObjectProp(
                        prop_name='object',
                        prop_value=object
                    )

                    if db_table:
                        parsed_objects_dict[hash_key].properties['db_table'] = CodeObjectProp(
                            prop_name='db_table',
                            prop_value=db_table
                        )

                if field_hash_key not in parsed_fields_dict:

                    parsed_field = CodeObjectField(
                        field_name=db_field,
                        field_type=field_type,
                        file=finding_file,
                        line=finding_line_int
                    )

                    parsed_objects_dict[hash_key].fields[db_field] = parsed_field
                    parsed_fields_dict[field_hash_key] = parsed_field

        
        if parsed_objects_dict:
            parsed_objects = list(parsed_objects_dict.values())

        logger.info(f"For scan {self.parser} data parse {len(parsed_objects)} objects")
        return parsed_objects