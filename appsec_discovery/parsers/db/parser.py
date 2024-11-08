import logging
import os
from typing import List
from pathlib import Path

from appsec_discovery.parsers import Parser
from appsec_discovery.models import CodeObject

logger = logging.getLogger(__name__)

class DbParser(Parser):

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


        logger.info(f"For scan {self.parser} data parse {len(parsed_objects)} objects")
        return parsed_objects