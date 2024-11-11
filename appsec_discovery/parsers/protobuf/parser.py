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
        return proto_files


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

            '''
            for type_def in file_proto.definitions:

                if type_def.kind == 'object_type_extension':
                    extend_types[type_def.name.value] = 1

                if type_def.name.value not in types:

                    types[type_def.name.value] = {
                        'name': type_def.name.value,
                        'type': type_def.kind,
                        'file': file,
                        'line': type_def.loc.start,
                        'fields': {}
                    }

                if hasattr(type_def, 'fields'):
                    for field_def in type_def.fields:

                        output = ''

                        if hasattr(field_def.type, 'name'):
                            output = field_def.type.name.value
                        elif hasattr(field_def.type, 'type') and hasattr(field_def.type.type, 'name'):
                            output = field_def.type.type.name.value
                        elif hasattr(field_def.type, 'type') and hasattr(field_def.type.type, 'type') and hasattr(field_def.type.type.type, 'name'):
                            output = field_def.type.type.type.name.value
                        elif hasattr(field_def.type, 'type') and hasattr(field_def.type.type, 'type') and hasattr(field_def.type.type.type, 'type') and hasattr(field_def.type.type.type.type, 'name'):
                            output = field_def.type.type.type.type.name.value

                        if field_def.name.value not in types[type_def.name.value]['fields']:
                            types[type_def.name.value]['fields'][field_def.name.value] = {
                                'name': field_def.name.value,
                                'file': file,
                                'line': field_def.loc.start,
                                'inputs': {},
                                'output': output, 
                            }

                        if hasattr(field_def, 'arguments'):
                            for input_def in field_def.arguments:
                                if input_def.name.value not in types[type_def.name.value]['fields'][field_def.name.value]['inputs']:

                                    input_type = ''
                                    if hasattr(input_def.type, 'name'):
                                        input_type = input_def.type.name.value
                                    elif hasattr(input_def.type, 'type') and hasattr(input_def.type.type, 'name'):
                                        input_type = input_def.type.type.name.value
                                    elif hasattr(input_def.type, 'type') and hasattr(input_def.type.type, 'type') and hasattr(input_def.type.type.type, 'name'):
                                        input_type = input_def.type.type.type.name.value
                                    elif hasattr(input_def.type, 'type') and hasattr(input_def.type.type, 'type') and hasattr(input_def.type.type.type, 'type') and hasattr(input_def.type.type.type.type, 'name'):
                                        input_type = input_def.type.type.type.type.name.value

                                    types[type_def.name.value]['fields'][field_def.name.value]['inputs'][input_def.name.value] = input_type
    

        for type_name, type_dict in types.items():

            if type_name in extend_types :

                for field_name, field in type_dict['fields'].items():

                    if field['output'] not in extend_types:
            
                        proto_type = 'Query'
                        proto_name = f"{type_name}.{field_name}"

                        if type_name in ['Query', 'Mutation']:
                            proto_type = type_name
                            proto_name = field_name
                        
                        elif 'Mutation' in types and types['Mutation']['fields']:
                            for mutation_field in types['Mutation']['fields'].values():
                                if mutation_field['output'] == type_name:
                                    proto_type = 'Mutation'

                        result_fields = {}

                        for input_name, input_type in field['inputs'].items():

                            if input_type in types and types[input_type]['fields']:

                                inputs_resolved = self.resolve_fields(input_type, types)

                                for input_resolved_name, input_resolved in inputs_resolved.items():

                                    result_fields[f"{input_name}.{input_resolved_name}"] = input_resolved
                            else:

                                result_fields[f"{input_name}"] = {
                                    'type': input_type,
                                    'file': field['file'],
                                    'line': field['line'],
                                }

                        if field['output'] in types and types[field['output']]['fields'] :

                            outputs_resolved = self.resolve_fields(field['output'], types)

                            for output_resolved_name, output_resolved in outputs_resolved.items():

                                result_fields[f"output.{output_resolved_name}"] = output_resolved

                        else:
                            result_fields["output"] = {
                                'type': field['output'],
                                'file': field['file'],
                                'line': field['line'],
                            }

                        unique_hash = self.calc_uniq_hash([field_name, proto_type, field['file']])

                        code_object = CodeObject(
                            hash=unique_hash,
                            object_name=f"{proto_type} {proto_name}",
                            object_type=proto_type.lower(),
                            parser=self.parser,
                            file=field['file'],
                            line=field['line'],
                            properties={},
                            fields={}
                        )

                        for result_field_name, result_field in result_fields.items():
                            code_object.fields[result_field_name] = CodeObjectField(
                                field_name=result_field_name,
                                field_type=result_field['type'],
                                file=result_field['file'],
                                line=result_field['line']
                            )

                        parsed_objects.append(code_object)
        '''

        logger.info(f"For scan {self.parser} data parse {len(parsed_objects)} objects")

        return parsed_objects