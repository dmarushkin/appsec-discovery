import logging
import os
from typing import List, Dict
from pathlib import Path

from appsec_discovery.parsers import Parser
from appsec_discovery.models import CodeObject, CodeObjectProp

logger = logging.getLogger(__name__)

class TerraformParser(Parser):

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

        for finding in semgrep_data:

            finding_file = finding.get('path')
            finding_line_int = finding.get('start',{}).get('line',0)

            rule_id = finding.get('check_id',"").split('.')[-1]

            vm_name = finding.get('extra').get('metavars').get('$...VM_NAME', {}).get('abstract_content',"")
            vm_domain = finding.get('extra').get('metavars').get('$...VM_DOMAIN', {}).get('abstract_content',"")
            vm_template = finding.get('extra').get('metavars').get('$...VM_TEMPLATE', {}).get('abstract_content',"")
            vm_pool = finding.get('extra').get('metavars').get('$...VM_POOL', {}).get('abstract_content',"")
            vm_desc = finding.get('extra').get('metavars').get('$...VM_DESC', {}).get('abstract_content',"")
            vm_server_cluster_name = finding.get('extra').get('metavars').get('$...VM_SERVER_CLUSTER_NAME', {}).get('abstract_content',"")
            vm_server_role = finding.get('extra').get('metavars').get('$...VM_SERVER_ROLE', {}).get('abstract_content',"")
            vm_server_owning_team = finding.get('extra').get('metavars').get('$...VM_SERVER_OWNING_TEAM', {}).get('abstract_content',"")
            vm_server_maintaining_team = finding.get('extra').get('metavars').get('$...VM_SERVER_MAINTAINING_TEAM', {}).get('abstract_content',"")
            vm_prometheus_env = finding.get('extra').get('metavars').get('$...VM_PROMETHEUS_ENV', {}).get('abstract_content',"")
            vlan_id = finding.get('extra').get('metavars').get('$...VLAN_ID', {}).get('abstract_content',"")
            dc = finding.get('extra').get('metavars').get('$...DC', {}).get('abstract_content',"")

            hash_key = self.calc_uniq_hash([finding_file, vm_name])

            if hash_key not in parsed_objects_dict:

                parsed_objects_dict[hash_key] = CodeObject(
                    hash=hash_key,
                    object_name=f"Virtual machine {vm_name}",
                    object_type="vm",
                    parser=self.parser,
                    file=finding_file,
                    line=finding_line_int,
                    properties={},
                    fields={}
                )

            if 'get-vm-name' in rule_id:
                parsed_objects_dict[hash_key].line = finding_line_int

            if vm_name :
                parsed_objects_dict[hash_key].properties['vm_name'] = CodeObjectProp(
                    prop_name='vm_name',
                    prop_value=vm_name
                )

            if vm_domain :
                parsed_objects_dict[hash_key].properties['vm_domain'] = CodeObjectProp(
                    prop_name='vm_domain',
                    prop_value=vm_domain
                )

                parsed_objects_dict[hash_key].object_name = f"Virtual machine {vm_name}.{vm_domain}"

            if vm_template :
                parsed_objects_dict[hash_key].properties['vm_template'] = CodeObjectProp(
                    prop_name='vm_template',
                    prop_value=vm_template
                ) 

            if vm_pool :
                parsed_objects_dict[hash_key].properties['vm_pool'] = CodeObjectProp(
                    prop_name='vm_pool',
                    prop_value=vm_pool
                )

            if vm_desc :
                parsed_objects_dict[hash_key].properties['vm_desc'] = CodeObjectProp(
                    prop_name='vm_desc',
                    prop_value=vm_desc
                )

            if vm_server_cluster_name :
                parsed_objects_dict[hash_key].properties['vm_server_cluster_name'] = CodeObjectProp(
                    prop_name='vm_server_cluster_name',
                    prop_value=vm_server_cluster_name
                )
                
            if vm_server_role :
                parsed_objects_dict[hash_key].properties['vm_server_role'] = CodeObjectProp(
                    prop_name='vm_server_role',
                    prop_value=vm_server_role
                )

            if vm_server_owning_team :
                parsed_objects_dict[hash_key].properties['vm_server_owning_team'] = CodeObjectProp(
                    prop_name='vm_server_owning_team',
                    prop_value=vm_server_owning_team
                )

            if vm_server_maintaining_team :
                parsed_objects_dict[hash_key].properties['vm_server_maintaining_team'] = CodeObjectProp(
                    prop_name='vm_server_maintaining_team',
                    prop_value=vm_server_maintaining_team
                )

            if vm_prometheus_env :
                parsed_objects_dict[hash_key].properties['vm_prometheus_env'] = CodeObjectProp(
                    prop_name='vm_prometheus_env',
                    prop_value=vm_prometheus_env
                )

            if vlan_id :
                parsed_objects_dict[hash_key].properties['vlan_id'] = CodeObjectProp(
                    prop_name='vlan_id',
                    prop_value=vlan_id
                )

            if dc :
                parsed_objects_dict[hash_key].properties['dc'] = CodeObjectProp(
                    prop_name='dc',
                    prop_value=dc
                )
        
        if parsed_objects_dict:
            parsed_objects = list(parsed_objects_dict.values())

        logger.info(f"For scan {self.parser} data parse {len(parsed_objects)} objects")
        return parsed_objects