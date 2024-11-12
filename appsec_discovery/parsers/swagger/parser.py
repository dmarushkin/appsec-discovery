import logging
import os
from typing import List
from pathlib import Path
from openapi_parser import parse

from appsec_discovery.parsers import Parser
from appsec_discovery.models import CodeObject, CodeObjectProp, CodeObjectField

logger = logging.getLogger(__name__)

class SwaggerParser(Parser):

    def find_swagger_files(self, root_dir):

        swagger_files = []
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml') or file.endswith('.json') :
                    try:
                        with open(os.path.join(root, file)) as file_obj:
                            file_str = file_obj.read()
                            if 'openapi' in file_str and 'paths' in file_str:
                                swagger_files.append(os.path.join(root, file))
                    except:
                        pass

        return swagger_files


    def run_scan(self) -> List[CodeObject]:

        objects_list: List[CodeObject] = []

        swagger_files = self.find_swagger_files(self.source_folder)
        swagger_data = {}

        for swagger_file in swagger_files:

            local_swagger_file = swagger_file.replace(self.source_folder, "")

            try:
                swagger_data[local_swagger_file] = parse(swagger_file)
            except Exception as ex:
                logger.error(f"Failed to parse {self.parser} for file {local_swagger_file}: {ex}")

        objects_list = self.parse_report(swagger_data)

        return objects_list

    def resolve_fields(self, type, object, file):
        
        resolved_fields = {}

        # Object
        if hasattr(object, 'properties'):

            for prop in object.properties:

                if not hasattr(prop.schema, 'items') and not hasattr(prop.schema, 'properties'):

                    resolved_fields[f"{type}.{prop.name}"] = CodeObjectField(
                        field_name=f"{type}.{prop.name}",
                        field_type=prop.schema.type.value,
                        file=file,
                        line=1
                    )
                
                else:

                    res_fields = self.resolve_fields(prop.name, prop.schema, file)

                    for field_name, field_data in res_fields.items():
                        resolved_fields[f"{type}.{field_name}"] = field_data
                        resolved_fields[f"{type}.{field_name}"].field_name = f"{type}.{field_name}"

        # List 
        elif hasattr(object, 'items'):

            res_fields = self.resolve_fields('', object.items, file)

            for field_name, field_data in res_fields.items():
                field_name = field_name.strip('.')
                resolved_fields[f"{type}.{field_name}"] = field_data
                resolved_fields[f"{type}.{field_name}"].field_name = f"{type}.{field_name}"
            
        else:
            resolved_fields[type] = CodeObjectField(
                field_name=type,
                field_type=object.type.value,
                file=file,
                line=1
            )

        return resolved_fields

    def parse_report(self, swagger_data) -> List[CodeObject]:

        parsed_objects: List[CodeObject] = []

        for file, file_spec in swagger_data.items():

            for path in file_spec.paths :

                for method in path.operations:

                    unique_hash = self.calc_uniq_hash([method.method.name, path.url, file])

                    code_object = CodeObject(
                        hash=unique_hash,
                        object_name=f"Route {path.url} ({method.method.name})",
                        object_type='route',
                        parser=self.parser,
                        file=file,
                        line=1,
                        properties={},
                        fields={}
                    )

                    code_object.properties['path'] = CodeObjectProp(
                        prop_name='path',
                        prop_value=path.url
                    )

                    code_object.properties['method'] = CodeObjectProp(
                        prop_name='method',
                        prop_value=method.method.name
                    )

                    for param in method.parameters:

                        code_object.fields[f"{param.location.value}.param.{param.name}"] = CodeObjectField(
                            field_name=f"{param.location.value}.param.{param.name}",
                            field_type=param.schema.type.value,
                            file=file,
                            line=1
                        )

                    if method.request_body :
                        for content in method.request_body.content :

                            res = self.resolve_fields('input', content.schema, file)

                            for field_name, field in res.items():
                                code_object.fields[field_name] = field

                    if method.responses :
                        for response in method.responses :
                            if response.content:
                                for content in response.content :

                                    res = self.resolve_fields('output', content.schema, file)

                                    for field_name, field in res.items():
                                        code_object.fields[field_name] = field

                    parsed_objects.append(code_object)
            
        logger.info(f"For scan {self.parser} data parse {len(parsed_objects)} objects")

        return parsed_objects
    









'''





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


'''