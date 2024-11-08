import logging
import os
from typing import List
from pathlib import Path

from appsec_discovery.parsers import Parser
from appsec_discovery.models import CodeObject

logger = logging.getLogger(__name__)

class GraphqlParser(Parser):

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

        '''

        objects_dict = {}

        for finding in semgrep_data:

            finding_file = finding.get('path')
            finding_line_int = finding.get('start',{}).get('line',0)

            type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"").strip("\"'![]")
            type_name = finding.get('extra').get('metavars').get('$TYPENAME', {}).get('abstract_content',"").strip("\"'![]")
            field_name = finding.get('extra').get('metavars').get('$FIELDNAME', {}).get('abstract_content',"").strip("\"'![]")
            input_name = finding.get('extra').get('metavars').get('$INPUTNAME', {}).get('abstract_content',"").strip("\"'![]")
            field_type = finding.get('extra').get('metavars').get('$FIELDTYPENAME', {}).get('abstract_content',"").strip("\"'![]")

            if type_name not in objects_dict:
                objects_dict[type_name] = {} # type fields

            if field_name not in objects_dict[type_name]:
                objects_dict[type_name][field_name] = {'input': input_name, 'type': field_type, 'file': finding_file, 'line': finding_line_int}

        if 'Query' in objects_dict and len(objects_dict['Query']) == 1 and objects_dict['Query'][0]['input'] is None:
            queries_root = 

        ''' 
        
        logger.info(f"For scan {self.parser} data parse {len(parsed_objects)} objects")
        return parsed_objects