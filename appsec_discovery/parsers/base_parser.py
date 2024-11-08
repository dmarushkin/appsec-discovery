
import logging
import subprocess
import json
import hashlib
from abc import ABC, abstractmethod
from typing import List
from appsec_discovery.models import CodeObject

logger = logging.getLogger(__name__)

class Parser(ABC):

    def __init__(self, parser, source_folder):

        self.parser = parser
        self.source_folder = source_folder

    @abstractmethod
    def parse_report(self, scanner_data) -> List[CodeObject]:
        pass

    @abstractmethod
    def run_scan(self) -> List[CodeObject]:
        pass

    def run_semgrep(self, source_folder: str, rules_folder: str):

        logger.info(f"Start {self.parser} scan for {source_folder}")

        try:
            result = subprocess.run(
                ["semgrep", "scan", "-f", rules_folder, "--json", "--metrics=off", "--no-git-ignore", source_folder],
                capture_output=True,
                text=True
            )

            if 'results' in result.stdout:

                semgrep_data = json.loads(result.stdout)

                normalized_results = []

                # save relative path
                for finding in semgrep_data.get('results',[]):

                    path = finding.get('path','')
                    finding['path'] = path.replace(source_folder, '')
                    normalized_results.append(finding)

                logger.info(f"End {self.parser} scan for {source_folder}, found {len(normalized_results)} rule hits")

                return normalized_results
            
            else:
                logger.error(f"Failed {self.parser} scan for {source_folder}: {result.stderr}")
        
        except Exception as ex:
            logger.error(f"Failed {self.parser} scan for {source_folder}: {ex}")
            
        return None        


    def calc_uniq_hash(self, prop_list: List[str]) -> str:

        hash_str = "#".join(prop_list)
        hash = hashlib.md5(hash_str.encode('utf-8')).hexdigest()

        return hash
