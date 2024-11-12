import logging
import os
from typing import List
import proto_schema_parser.parser as pb_parser
from proto_schema_parser.ast import Package, Service, Message, Method, Field

from appsec_discovery.parsers import Parser
from appsec_discovery.models import CodeObject, CodeObjectField

logger = logging.getLogger(__name__)

class ProtobufParser(Parser):

    def find_proto_files(self, root_dir):
        proto_files = []
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.proto'):
                    proto_files.append(os.path.join(root, file))
        return sorted(proto_files)


    def run_scan(self) -> List[CodeObject]:

        objects_list: List[CodeObject] = []

        proto_files = self.find_proto_files(self.source_folder)
        proto_data = {}

        for proto_file in proto_files:

            local_proto_file = proto_file.replace(self.source_folder, "")

            try:
                with open(proto_file) as file:
                    file_str = file.read()
                    proto_data[local_proto_file] = pb_parser.Parser().parse(file_str)
            except Exception as ex:
                logger.error(f"Failed to parse {self.parser} for file {local_proto_file}: {ex}")

        objects_list = self.parse_report(proto_data)

        return objects_list

    def resolve_fields(self, type_name, messages, file):
        
        resolved_fields = {}

        local_messages = {}

        for el in messages[type_name].elements:       
            if isinstance(el, Message) and el.name not in local_messages:
                local_messages[el.name] = el

        for el in messages[type_name].elements:      
            if isinstance(el, Field) and el.name not in resolved_fields:

                if el.type in messages:
                    resolved_local_fields = self.resolve_fields(el.type, messages, file)

                    for field_name, field in resolved_local_fields.items():
                        resolved_fields[f"{type_name}.{el.name}.{field_name}"] = field

                elif el.type in local_messages:
                    resolved_local_fields = self.resolve_fields(el.type, local_messages, file)

                    for field_name, field in resolved_local_fields.items():
                        resolved_fields[f"{type_name}.{el.name}.{field_name}"] = field

                else:
                    resolved_fields[f"{type_name}.{el.name}"] = CodeObjectField(
                        field_name=f"{type_name}.{el.name}",
                        field_type=el.type,
                        file=file,
                        line=el.number
                    )

        if not resolved_fields :
            resolved_fields[type_name] = CodeObjectField(
                        field_name=type_name,
                        field_type='Empty',
                        file=file,
                        line=1
                    )

        return resolved_fields

    def parse_report(self, proto_data) -> List[CodeObject]:

        parsed_objects: List[CodeObject] = []

        packages = {}

        for file, file_proto in proto_data.items():

            cur_package = ''

            for el in file_proto.file_elements:

                if isinstance(el, Package) :

                    cur_package = el.name

                    if el.name not in packages:
                        packages[el.name] = {
                            'services': {},
                            'messages': {},
                            'file': file
                        }

            for el in file_proto.file_elements:

                if isinstance(el, Service) and el.name not in packages[cur_package]['services']:
                    packages[cur_package]['services'][el.name] = {}

                    for service_method in el.elements:
                        if isinstance(service_method, Method) and service_method.name not in packages[cur_package]['services'][el.name]:
                            packages[cur_package]['services'][el.name][service_method.name] = {
                                'input': service_method.input_type.type,
                                'output': service_method.output_type.type
                            }
                
                if isinstance(el, Message) and el.name not in packages[cur_package]['messages']:
                    packages[cur_package]['messages'][el.name] = el
        

        for package_name, package in packages.items():
            for service_name, service in package['services'].items():
                for method_name, method in service.items():

                    unique_hash = self.calc_uniq_hash([package['file'], package_name, service_name, method_name])

                    code_object = CodeObject(
                        hash=unique_hash,
                        object_name=f"Rpc /{package_name}.{service_name}/{method_name}",
                        object_type='rpc',
                        parser=self.parser,
                        file=package['file'],
                        line=1,
                        properties={},
                        fields={}
                    )

                    if method['input'] in package['messages']:
                        input_fields = self.resolve_fields(method['input'], package['messages'], package['file'])

                        for field_name, field in input_fields.items():    
                            code_object.fields[f"input.{field_name}"] = field
                    else:
                        code_object.fields['input'] = CodeObjectField(
                            field_name='input',
                            field_type=method['input'],
                            file=package['file'],
                            line=1
                        )

                    if method['output'] in package['messages']:
                        output_fields = self.resolve_fields(method['output'], package['messages'], package['file'])

                        for field_name, field in output_fields.items():    
                            code_object.fields[f"output.{field_name}"] = field
                    else:
                        code_object.fields['output'] = CodeObjectField(
                            field_name='output',
                            field_type=method['output'],
                            file=package['file'],
                            line=1
                        )

                    parsed_objects.append(code_object)

        logger.info(f"For scan {self.parser} data parse {len(parsed_objects)} objects")

        return parsed_objects