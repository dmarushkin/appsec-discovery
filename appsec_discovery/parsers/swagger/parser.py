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

        return sorted(swagger_files)


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