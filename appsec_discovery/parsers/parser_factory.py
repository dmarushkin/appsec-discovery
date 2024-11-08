from appsec_discovery.parsers.base_parser import Parser

import logging
import os
from importlib import import_module
from importlib.util import find_spec
from inspect import isclass
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

class ParserFactory:

    @staticmethod
    def get_parser(parser_type: str):

        package_dir = str(Path(__file__).resolve().parent)

        for module_name in os.listdir(package_dir):

            if os.path.isdir(os.path.join(package_dir, module_name)) and parser_type == module_name:

                try:
                    # check if it's a Python module
                    if find_spec(f"appsec_discovery.parsers.{module_name}.parser"):

                        module = import_module(f"appsec_discovery.parsers.{module_name}.parser")

                        for attribute_name in dir(module):

                            attribute = getattr(module, attribute_name)
                            if isclass(attribute) and 'parser' in attribute_name.lower() and attribute_name != 'Parser':

                                parser = attribute
                                logger.info(f"Found parser {parser.__qualname__} in appsec_discovery.parsers.{module_name}.parser")
                                
                                return parser
                except Exception as ex:
                    logger.error(f"Failed to find parser for type {parser_type}: {ex}")

        logger.error(f"Parser for type {parser_type} not found")
        return None
    
    @staticmethod
    def get_parser_types() -> List[str]:

        parsers_list = []

        package_dir = str(Path(__file__).resolve().parent)

        for module_name in os.listdir(package_dir):

            if os.path.isdir(os.path.join(package_dir, module_name)) :

                try:
                    # check if it's a Python module
                    if find_spec(f"appsec_discovery.parsers.{module_name}.parser"):

                        module = import_module(f"appsec_discovery.parsers.{module_name}.parser")

                        for attribute_name in dir(module):

                            attribute = getattr(module, attribute_name)
                            if isclass(attribute) and 'parser' in attribute_name.lower() and attribute_name != 'Parser':
                                parsers_list.append(module_name)

                except:
                    logger.exception(f"failed to load {module_name}")

        return parsers_list