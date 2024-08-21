from logger import get_logger
from datetime import datetime
import os
from  os import path
import subprocess
import json
import re

from models import Scan, TableObject, ProtoObject, ClientObject, TfObject

from services.gl_service import (
    clone_gitlab_project_code,
    get_gitlab_project_lang
)
from services.db_service import (
    insert_scan, 
    get_scan,
    upsert_table_obj,
    upsert_proto_obj,
    upsert_client_obj,
    upsert_tf_obj,
    get_score_rules,
    get_client_fields
)

from services.alert_service import render_and_send_alert

from services.score_service import score_field

logger = get_logger(__name__)

def scan_branch(session, branch):

    project_id = branch.project_id
    project_path = branch.project_path
    branch_name = branch.branch_name
    branch_id = branch.id
    branch_commit = branch.commit

    project_lang = get_gitlab_project_lang(project_path, branch_name) 

    if clone_gitlab_project_code(project_path, branch_name, project_id, branch_id, branch_commit) :
      
        if project_lang == 'go': 

            score_rules = get_score_rules(session)
            
            scan = Scan(
                scanner='db_scan',
                rules_version='1.0.0',
                project_id=project_id,
                branch_id=branch_id,
                branch_commit=branch_commit,
                scanned_at=datetime.now()
            )

            if not get_scan(session, scan.scanner, scan.rules_version, project_id, branch_id, branch_commit):
                
                db_objects_list, result = run_db_scan(project_path, project_id, branch_id, branch_commit, score_rules)

                for table_object in db_objects_list:
                    upsert_table_obj(session, table_object)

                if result == 'scanned':
                    insert_scan(session, scan)
            else:
                logger.info(f"Already exist scan {scan.scanner} for {project_path}, branch {branch_name} scanned")

            scan = Scan(
                scanner='proto_scan',
                rules_version='1.0.0',
                project_id=project_id,
                branch_id=branch_id,
                branch_commit=branch_commit,
                scanned_at=datetime.now()
            )

            if not get_scan(session, scan.scanner, scan.rules_version, project_id, branch_id, branch_commit):
                
                proto_objects_list, result = run_proto_scan(project_path, project_id, branch_id, branch_commit, score_rules)

                for proto_object in proto_objects_list:
                    upsert_proto_obj(session, proto_object)

                if result == 'scanned':
                    insert_scan(session, scan)
            else:
                logger.info(f"Already exist scan {scan.scanner} for {project_path}, branch {branch_name} scanned")

            scan = Scan(
                scanner='client_scan',
                rules_version='1.0.0',
                project_id=project_id,
                branch_id=branch_id,
                branch_commit=branch_commit,
                scanned_at=datetime.now()
            )

            if not get_scan(session, scan.scanner, scan.rules_version, project_id, branch_id, branch_commit):
                
                client_objects_list, result = run_client_scan(session, project_path, project_id, branch_id, branch_commit, score_rules)

                for client_object in client_objects_list:
                    upsert_client_obj(session, client_object)

                if result == 'scanned':
                    insert_scan(session, scan)
            else:
                logger.info(f"Already exist scan {scan.scanner} for {project_path}, branch {branch_name} scanned")

        if 'terraform' in project_path:

            scan = Scan(
                scanner='tf_scan',
                rules_version='1.0.0',
                project_id=project_id,
                branch_id=branch_id,
                branch_commit=branch_commit,
                scanned_at=datetime.now()
            )

            if not get_scan(session, scan.scanner, scan.rules_version, project_id, branch_id, branch_commit):
                
                tf_objects_list, result = run_tf_scan(project_path, project_id, branch_id, branch_commit)

                for tf_object in tf_objects_list:
                    upsert_tf_obj(session, tf_object)

                if result == 'scanned':
                    insert_scan(session, scan)
            else:
                logger.info(f"Already exist scan {scan.scanner} for {project_path}, branch {branch_name} scanned")
    
    logger.info(f"Project {project_path}, branch {branch_name} scanned")
    
    return 'scanned'


def scan_mr(session, project_id, project_path, mr_id,
            source_branch_name, source_branch_id, source_branch_commit,
            target_branch_name, target_branch_id, target_branch_commit):
    
    project_lang = get_gitlab_project_lang(project_path, target_branch_name)
        
    if clone_gitlab_project_code(project_path, target_branch_name, project_id, target_branch_id, target_branch_commit) :

        if project_lang == 'go':

            new_crit_objects = {'table_objs': {}, 'proto_objs': {}, 'client_objs': {}}

            score_rules = get_score_rules(session)

            clone_gitlab_project_code(project_path, source_branch_name, project_id, source_branch_id, source_branch_commit)

            scan = Scan(
                scanner='db_scan',
                rules_version='1.0.0',
                project_id=project_id,
                branch_id=source_branch_id,
                branch_commit=source_branch_commit,
                scanned_at=datetime.now()
            )
                
            source_objects_list, _ = run_db_scan(project_path, project_id, source_branch_id, source_branch_commit, score_rules)
            target_objects_list, _ = run_db_scan(project_path, project_id, target_branch_id, target_branch_commit, score_rules)
  
            diff_objects_db = get_diff(scan.scanner, source_objects_list, target_objects_list) 

            for table_object in diff_objects_db:
                _, result = upsert_table_obj(session, table_object)
                if result == 'inserted' and table_object.score > 0:
                    uniq_key = f"{table_object.table_name} - {table_object.field}"
                    new_crit_objects['table_objs'][uniq_key] = table_object
            
            scan.scanned_at 
            insert_scan(session, scan)

            scan = Scan(
                scanner='proto_scan',
                rules_version='1.0.0',
                project_id=project_id,
                branch_id=source_branch_id,
                branch_commit=source_branch_commit,
                scanned_at=datetime.now()
            )
                
            source_objects_list, _ = run_proto_scan(project_path, project_id, source_branch_id, source_branch_commit, score_rules)
            target_objects_list, _ = run_proto_scan(project_path, project_id, target_branch_id, target_branch_commit, score_rules)
  
            diff_objects_proto = get_diff(scan.scanner, source_objects_list, target_objects_list) 

            for proto_object in diff_objects_proto:
                _, result = upsert_proto_obj(session, proto_object)
                if result == 'inserted' and proto_object.score > 0:
                    uniq_key = f"{proto_object.package} - {proto_object.service} - {proto_object.method} - {proto_object.message} - {proto_object.field}"
                    new_crit_objects['proto_objs'][uniq_key] = proto_object

            insert_scan(session, scan)

            scan = Scan(
                scanner='client_scan',
                rules_version='1.0.0',
                project_id=project_id,
                branch_id=source_branch_id,
                branch_commit=source_branch_commit,
                scanned_at=datetime.now()
            )
                
            source_objects_list, _ = run_client_scan(session, project_path, project_id, source_branch_id, source_branch_commit, score_rules)
            target_objects_list, _ = run_client_scan(session, project_path, project_id, target_branch_id, target_branch_commit, score_rules)
  
            diff_objects = get_diff(scan.scanner, source_objects_list, target_objects_list) 
            
            # save objects to alert
            for client_object in diff_objects:
                _, result = upsert_client_obj(session, client_object)   
                if result == 'inserted' and client_object.score > 0:
                    uniq_key = f"{client_object.package} - {client_object.method} - {client_object.client_url}"
                    new_crit_objects['client_objs'][uniq_key] = client_object

            insert_scan(session, scan)

            if new_crit_objects['table_objs'] or new_crit_objects['proto_objs'] or new_crit_objects['client_objs']:

                logger.info(f"Found {len(new_crit_objects['table_objs']) + len(new_crit_objects['proto_objs']) + len(new_crit_objects['client_objs']) } objects to alert")

                render_and_send_alert(project_path, source_branch_name, mr_id, new_crit_objects)

    return 'scanned'


def get_diff(scanner, source_objects, target_objects):

    diff_objects = []

    to_keys = {}    

    if scanner == 'db_scan':

        for to in target_objects:
            to_key = f"{to.table_name} - {to.field}"
            to_keys[to_key] = 1

        for so in source_objects:

            so_key = f"{so.table_name} - {so.field}"

            if so_key not in to_keys:
                diff_objects.append(so)
                

    if scanner == 'proto_scan':

        for to in target_objects:
            to_key = f"{to.package} - {to.service} - {to.method} - {to.message} - {to.field}"
            to_keys[to_key] = 1

        for so in source_objects:

            so_key = f"{so.package} - {so.service} - {so.method} - {so.message} - {so.field}"

            if so_key not in to_keys:
                diff_objects.append(so)
            
    if scanner == 'client_scan':

        for to in target_objects:
            to_key = f"{to.package} - {to.method} - {to.client_url}"
            to_keys[to_key] = 1

        for so in source_objects:
            so_key = f"{so.package} - {so.method} - {so.client_url}"
            if so_key not in to_keys:
                diff_objects.append(so)

    logger.info(f"Found {len(diff_objects)} new objects in {scanner} diff")

    return diff_objects

#######################################
##  SQL DB Objects                  ###
#######################################

def list_files_sorted(directory):
    try:
        files = os.listdir(directory)
        files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
        files.sort()

        return files
    except Exception as e:
        return []
    
def find_migrations_dir(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if 'migrations' in dirs:
            return os.path.join(root, 'migrations')
    return None

def find_schema_sql(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if 'schema.sql' in files:
            return os.path.join(root, 'schema.sql')
    return None

def run_db_scan(project_path, project_id, branch_id, branch_commit, score_rules):

    # Determine the local path for the clone
    project_local_path = f"{str(project_id)}/{str(branch_id)}/{branch_commit}"

    code_folder = f"code/{project_local_path}"

    migrations_path = find_migrations_dir(code_folder)
    schema_sql_path = find_schema_sql(code_folder)

    sorted_files = []

    if migrations_path:
        sorted_files += [f"{migrations_path}/{file}" for file in list_files_sorted(migrations_path)]

    if schema_sql_path:
        sorted_files.append(schema_sql_path)

    # remove goose artifacts

    for file in sorted_files:

        with open(file, 'r') as file_obj:
            file_content = file_obj.read()

        if 'goose StatementBegin' in file_content:
            up_statements = re.findall(r'-- \+goose Up\n(.*?)\n-- \+goose Down', file_content, re.DOTALL)
            extracted_statements = '\n'.join(up_statements).strip().upper()
        else:
            extracted_statements = file_content

        with open(file, 'w') as file_obj:
            file_obj.write(extracted_statements)
        
        file_name = file.replace(code_folder,"")

        logger.info(f"db scan prepared file {file_name}")

    # run semgrep on all files 

    semgrep_results_per_file = {}

    for file in sorted_files:
        semgrep_results_per_file[file] = []

    if sorted_files:

        result = subprocess.run(
            ["semgrep", "-f", "sg_rules/parse-sql.yaml", "--json", "--metrics=off"] + sorted_files,
            capture_output=True,
            text=True
        )

        semgrep_data = json.loads(result.stdout)

        logger.info(f"db scan found {len(semgrep_data['results'])} objects")

        for finding in semgrep_data['results']:
            
            finding_file = finding.get('path')
            semgrep_results_per_file[finding_file].append(finding)

    # process results by sorted files

    database_objects = {}

    for db_file in sorted_files:

        file = db_file.replace(code_folder,"") 

        for finding in semgrep_results_per_file[db_file]:

            rule_id = finding.get('check_id',"").split('.')[-1]

            table = finding.get('extra').get('metavars').get('$TABLE_NAME', {}).get('abstract_content',"").lower()
            field = finding.get('extra').get('metavars').get('$FIELD', {}).get('abstract_content',"").lower()
            type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"").lower()
            comment = finding.get('extra').get('metavars').get('$...COMMENT', {}).get('abstract_content',"").lower()

            rule_id = finding.get('check_id',"").split('.')[-1]

            line = finding.get('start',{}).get('line',0)

            if 'create-table' in rule_id:

                if table not in database_objects:
                    database_objects[table] = {'schema': {},
                                            'comment': comment,
                                            'file': file,
                                            'line': line}

                if field not in database_objects[table]['schema']:
                    database_objects[table]['schema'][field] = {'field': field,
                                                                'comment': comment,
                                                                'type': type,
                                                                'file': file,
                                                                'line': line}
                    
            if 'add-columns' in rule_id:

                if table not in database_objects:
                    database_objects[table] = {'schema': {},
                                               'comment': comment,
                                            'file': file,
                                            'line': line}

                if field not in database_objects[table]['schema']:
                    database_objects[table]['schema'][field] = {'field': field,
                                                                'comment': comment,
                                                                'type': type,
                                                                'file': file,
                                                                'line': line}
    
            if 'drop-table' in rule_id:
                if table in database_objects:
                    database_objects.pop(table, None)


            if 'drop-columns' in rule_id:
                if table in database_objects:
                    if field in database_objects[table]['schema']:
                        database_objects[table]['schema'].pop(field, None)

            if 'table-comments' in rule_id:
                if table in database_objects and comment:
                    database_objects[table]['comment'] = comment

            if 'table-column-comments' in rule_id:
                if table in database_objects:
                    if field in database_objects[table]['schema'] and comment:
                        database_objects[table]['schema'][field]['comment'] = comment
    
        
        logger.info(f"db scan processed file {file}")

    table_objects = []

    for table_name, table_data in database_objects.items():
        for val in table_data['schema'].values():
            if val['field'] not in ['if']:
                teble_obj = TableObject(
                    project_id=project_id,
                    branch_id=branch_id,
                    table_name=table_name,
                    table_comment=table_data['comment'],
                    field=val['field'],
                    field_comment=val['comment'],
                    type=val['type'],
                    file=val['file'],
                    line=val['line'],
                    score=score_field(project_path,table_name,'table',val['field'],val['type'],score_rules)
                )

            table_objects.append(teble_obj)

    logger.info(f"db scan found {len(database_objects)} tables and {len(table_objects)} fields")

    return table_objects, 'scanned'


#######################################
##  Proto Objects                   ###
#######################################

def find_proto_files(root_dir):
    proto_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.proto'):
                proto_files.append(os.path.join(root, file))
    return proto_files


def run_proto_scan(project_path, project_id, branch_id, branch_commit, score_rules):

    # Determine the local path for the clone
    project_local_path = f"{str(project_id)}/{str(branch_id)}/{branch_commit}"

    code_folder = f"code/{project_local_path}"

    proto_files = find_proto_files(code_folder)

    semgrep_results_per_file = {}

    for file in proto_files:
        semgrep_results_per_file[file] = []

    if proto_files:

        result = subprocess.run(
            ["semgrep", "-f", "sg_rules/parse-proto.yaml", "--json", "--metrics=off"] + proto_files,
            capture_output=True,
            text=True
        )

        semgrep_data = json.loads(result.stdout)

        logger.info(f"proto scan found {len(semgrep_data['results'])} objects")

        for finding in semgrep_data['results']:
            finding_file = finding.get('path')
            semgrep_results_per_file[finding_file].append(finding)

    proto_objects = []

    for proto_file in proto_files:

        file = proto_file.replace(code_folder,"")

        messages_for_lines = {}

        child_enums = {}

        root_enums = {}

        relative_messages = {}

        uniq_messages = []

        package = ""

        routes = {}

        # find package

        for finding in semgrep_results_per_file[proto_file]:
            
            rule_id = finding.get('check_id',"").split('.')[-1]

            if 'get-package' in rule_id:
                package = finding.get('extra').get('metavars').get('$...PACKAGE', {}).get('abstract_content',"").strip()


        for finding in semgrep_data['results']:

            rule_id = finding.get('check_id',"").split('.')[-1]
                    
            if 'get-service-routes' in rule_id:

                service = finding.get('extra').get('metavars').get('$SERVICE', {}).get('abstract_content',"")
                method = finding.get('extra').get('metavars').get('$METHOD', {}).get('abstract_content',"")
                method_comment = finding.get('extra').get('metavars').get('$...COMMENT', {}).get('abstract_content',"").strip()
                input = finding.get('extra').get('metavars').get('$INPUT', {}).get('abstract_content',"")
                output = finding.get('extra').get('metavars').get('$OUTPUT', {}).get('abstract_content',"")

                if method_comment:
                    line_int = finding.get('start',{}).get('line',0) + 1
                else:
                    line_int = finding.get('start',{}).get('line',0) 

                url = f"/{package}.{service}/{method}"

                if url in routes and method_comment:
                    routes[url]['method_comment'] = method_comment
                else:
                    routes[url] = {
                        'file': file,  
                        'line': line_int,
                        'url': url,
                        'package': package,
                        'service': service,
                        'method': method,
                        'method_comment': method_comment,
                        'input': input, 
                        'output': output
                    }

            if 'get-messages' in rule_id:

                message = finding.get('extra').get('metavars').get('$MESSAGE', {}).get('abstract_content',"")
                field = finding.get('extra').get('metavars').get('$FIELD', {}).get('abstract_content',"")
                field_comment = finding.get('extra').get('metavars').get('$...COMMENT', {}).get('abstract_content',"").strip()
                type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"")
                ext = finding.get('extra').get('metavars').get('$EXT', {}).get('abstract_content',"")

                if field_comment:
                    line = str(finding.get('start',{}).get('line',0) + 1)
                else:
                    line = str(finding.get('start',{}).get('line',0))

                uniq_messages.append(message)

                if line not in messages_for_lines:
                    messages_for_lines[line] = [message]
                else:
                    if message not in messages_for_lines[line]:
                        messages_for_lines[line].append(message)

                if len(messages_for_lines[line]) > 1 :
                    for each1 in messages_for_lines[line]:
                        for each2 in messages_for_lines[line]:
                            if each1 != each2:
                                if each1 not in relative_messages:
                                    relative_messages[each1] = [each2]
                                else:
                                    if each2 not in relative_messages[each1]:
                                        relative_messages[each1].append(each2)
                                            
            if 'get-child-enums' in rule_id:

                parrent_message = finding.get('extra').get('metavars').get('$PARRENT', {}).get('abstract_content',"")
                child_enum = finding.get('extra').get('metavars').get('$CHILD', {}).get('abstract_content',"")

                if parrent_message not in child_enums:
                    child_enums[parrent_message] = child_enum

            if 'get-root-enums' in rule_id:

                enum = finding.get('extra').get('metavars').get('$ENUM', {}).get('abstract_content',"")

                if enum not in root_enums:
                    root_enums[enum] = enum

        # Resolve all parrent to child messages

        child_messages = {}

        for finding in semgrep_data['results']:
            
            rule_id = finding.get('check_id',"").split('.')[-1]

            if 'get-messages' in rule_id:

                message = finding.get('extra').get('metavars').get('$MESSAGE', {}).get('abstract_content',"")
                field = finding.get('extra').get('metavars').get('$FIELD', {}).get('abstract_content',"")
                type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"")
                ext = finding.get('extra').get('metavars').get('$EXT', {}).get('abstract_content',"")
        
                if message in relative_messages and type in relative_messages[message]:
                    if message not in child_messages:
                        child_messages[message] = [type]
                    else:
                        if type not in child_messages[message]:
                            child_messages[message].append(type)

        
        child_message_schemas = {}

        message_schemas = {}

        for finding in semgrep_data['results']:
            
            rule_id = finding.get('check_id',"").split('.')[-1]

            if 'get-messages' in rule_id:

                message = finding.get('extra').get('metavars').get('$MESSAGE', {}).get('abstract_content',"")
                field = finding.get('extra').get('metavars').get('$FIELD', {}).get('abstract_content',"")
                field_comment = finding.get('extra').get('metavars').get('$...COMMENT', {}).get('abstract_content',"")
                type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"")
                ext = finding.get('extra').get('metavars').get('$EXT', {}).get('abstract_content',"")

                if field_comment:
                    line = str(finding.get('start',{}).get('line',0) + 1)
                    line_int = finding.get('start',{}).get('line',0) + 1
                else:
                    line = str(finding.get('start',{}).get('line',0))
                    line_int = finding.get('start',{}).get('line',0)                 

                if len(messages_for_lines[line]) > 1 :

                    child_message = ''

                    if message in child_messages:
                        for child in messages_for_lines[line] :
                            if child in child_messages[message]:
                                child_message = child

                    if message not in child_message_schemas :
                        child_message_schemas[message] = {}

                    if child_message not in child_message_schemas[message] :
                        child_message_schemas[message][child_message] = {}
                        
                    if field not in child_message_schemas[message][child_message] :
                        child_message_schemas[message][child_message][field] = {'field': field,
                                                                                'field_comment': field_comment,
                                                                                'type': type,
                                                                                'file': file,
                                                                                'line': line_int}
                        
                    if field in child_message_schemas[message][child_message] and field_comment:
                        child_message_schemas[message][child_message][field]['field_comment'] = field_comment

                else:
                    
                    if message not in message_schemas :
                        message_schemas[message] = {}

                    if ext :

                        ext_type = f"external.{ext}.{type}"

                        if ext_type.startswith("external.protobuf."):
                            ext_type = type

                        message_schemas[message][field] = {'field': field,
                                                         'field_comment': field_comment,
                                                        'type': ext_type,
                                                        'file': file,
                                                        'line': line_int}
                        
                    else:

                        if message in child_enums \
                            and type in child_enums[message] \
                            and field not in message_schemas[message] :
                            message_schemas[message][field] = {'field': field,
                                                            'field_comment': field_comment,
                                                            'type': 'enum',
                                                            'file': file,
                                                            'line': line_int}

                        if type in root_enums \
                            and field not in message_schemas[message] :
                            message_schemas[message][field] = {'field': field,
                                                            'field_comment': field_comment,
                                                            'type': 'enum',
                                                            'file': file,
                                                            'line': line_int}
                            
                        if type not in uniq_messages \
                            and field not in message_schemas[message]:
                            message_schemas[message][field] = {'field': field,
                                                            'field_comment': field_comment,
                                                            'type': type,
                                                            'file': file,
                                                            'line': line_int}
                            
                        if field in message_schemas[message] and field_comment:
                            message_schemas[message][field]['field_comment'] = field_comment


                        
        for finding in semgrep_data['results']:
        
            rule_id = finding.get('check_id',"").split('.')[-1]

            if 'get-messages' in rule_id:

                message = finding.get('extra').get('metavars').get('$MESSAGE', {}).get('abstract_content',"")
                field = finding.get('extra').get('metavars').get('$FIELD', {}).get('abstract_content',"")
                type = finding.get('extra').get('metavars').get('$TYPE', {}).get('abstract_content',"")

                line_int = finding.get('start',{}).get('line',0)

                if len(messages_for_lines[line]) == 1 :

                    if message not in message_schemas :
                        message_schemas[message] = {}

                    if message in child_message_schemas and type in child_message_schemas[message]:

                        for child_field, child_field_val in child_message_schemas[message][type].items():
                            field_path = f"{field}.{type}.{child_field}"
                            message_schemas[message][field_path] = {'field': field_path,
                                                                    'field_comment': child_field_val['field_comment'],
                                                                    'type': child_field_val['type'],
                                                                    'file': child_field_val['file'],
                                                                    'line': child_field_val['line']}

                    if type in message_schemas:

                        for child_field, child_field_val in message_schemas[type].copy().items():
                            field_path = f"{field}.{type}.{child_field}"
                            message_schemas[message][field_path] = {'field': field_path,
                                                                    'field_comment': child_field_val['field_comment'],
                                                                    'type': child_field_val['type'],
                                                                    'file': child_field_val['file'],
                                                                    'line': child_field_val['line']}
                            

                            
        for route_path, route_data in routes.copy().items():

            if route_data['input'] in message_schemas:
                routes[route_path]['input_schema'] = message_schemas[route_data['input']]
            else:
                routes[route_path]['input_schema'] = {'empty': {'field': 'empty',
                                                                'field_comment': None,
                                                                'type': 'empty',
                                                                'file': file,
                                                                'line': 0}}
            
            if route_data['output'] in message_schemas:
                routes[route_path]['output_schema'] = message_schemas[route_data['output']]
            else:
                routes[route_path]['output_schema'] = {'empty': {'field': 'empty', 
                                                                'field_comment': None,
                                                                'type': 'empty',
                                                                'file': file,
                                                                'line': 0}}

        for route_path, route_data in routes.items():

            for route_field, route_field_data in route_data['input_schema'].items():
                proto_object = ProtoObject(
                    project_id=project_id,
                    branch_id=branch_id,
                    url=route_path,
                    package=route_data['package'],
                    service=route_data['service'],
                    method=route_data['method'],
                    method_comment=route_data['method_comment'],
                    message=route_data['input'],
                    message_type='input',
                    field=route_field_data['field'],
                    field_comment=route_field_data['field_comment'],
                    type=route_field_data['type'],
                    file=route_field_data['file'],
                    line=route_field_data['line'],
                    score=score_field(project_path,route_path,'proto',route_field_data['field'],route_field_data['type'],score_rules)
                )

                proto_objects.append(proto_object)

            for route_field, route_field_data in route_data['output_schema'].items():
                proto_object = ProtoObject(
                    project_id=project_id,
                    branch_id=branch_id,
                    url=route_path,
                    package=route_data['package'],
                    service=route_data['service'],
                    method=route_data['method'],
                    method_comment=route_data['method_comment'],
                    message=route_data['output'],
                    message_type='output',
                    field=route_field_data['field'],
                    field_comment=route_field_data['field_comment'],
                    type=route_field_data['type'],
                    file=route_field_data['file'],
                    line=route_field_data['line'],
                    score=score_field(project_path,route_path,'proto',route_field_data['field'],route_field_data['type'],score_rules)
                )

                proto_objects.append(proto_object)

        logger.info(f"proto scan processed file {file}")

        logger.info(f"proto scan found {len(routes)} methods and {len(proto_objects)} fields")

    return proto_objects, 'scanned'

#######################################
##  Ext Clients Calls               ###
#######################################     

def find_ext_client_files(root_dir):
    ext_client_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('_grpc.pb.go'):
                ext_client_files.append(os.path.join(root, file))
    return ext_client_files

def find_all_pkg_files(root_dir):
    pkg_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if not file.endswith('_test.go') and file.endswith('.go') \
               and 'mocks' not in file and 'mock_' not in file and '_mock' not in file:
                pkg_files.append(os.path.join(root, file))
    return pkg_files


def run_client_scan(session, project_path, project_id, branch_id, branch_commit, score_rules):

    # Determine the local path for the clone
    project_local_path = f"{str(project_id)}/{str(branch_id)}/{branch_commit}"

    code_folder = f"code/{project_local_path}"

    client_files = find_ext_client_files(f"{code_folder}/internal/pb")

    semgrep_results_per_file = {}

    for file in client_files:
        semgrep_results_per_file[file] = []

    if client_files:

        result = subprocess.run(
            ["semgrep", "-f", "sg_rules/parse-clients.yaml", "--json", "--metrics=off"] + client_files,
            capture_output=True,
            text=True
        )

        semgrep_data = json.loads(result.stdout)

        logger.info(f"client scan found {len(semgrep_data['results'])} objects")

        for finding in semgrep_data['results']:
            finding_file = finding.get('path')
            semgrep_results_per_file[finding_file].append(finding)


    ext_clients = {}

    for client_file in client_files:

        file = client_file.replace(code_folder,"")

        package = ""

        client = ""

        # Getting package

        for finding in semgrep_results_per_file[client_file]:

            rule_id = finding.get('check_id',"").split('.')[-1]
                    
            if 'get-package-from-service' in rule_id:

                package = finding.get('extra').get('metavars').get('$PACKAGE', {}).get('abstract_content',"")
                break
        
        for finding in semgrep_results_per_file[client_file]:

            rule_id = finding.get('check_id',"").split('.')[-1]
                    
            if 'get-methods-from-client' in rule_id:

                client = finding.get('extra').get('metavars').get('$CLIENT', {}).get('abstract_content',"")
                method = finding.get('extra').get('metavars').get('$METHOD', {}).get('abstract_content',"")
                input = finding.get('extra').get('metavars').get('$INPUT', {}).get('abstract_content',"")
                output = finding.get('extra').get('metavars').get('$OUTPUT', {}).get('abstract_content',"")

                line = finding.get('start',{}).get('line',0)

                # make dict package.client => method => data

                if client not in ext_clients:
                    ext_clients[client] = {}

                if method not in ext_clients[client]:
                    ext_clients[client][method] = {'file': file,
                                                    'line': line,
                                                    'url': "",
                                                    'method': method,
                                                    'input': input,
                                                    'output': output}

        for finding in semgrep_results_per_file[client_file]:

            rule_id = finding.get('check_id',"").split('.')[-1]
                    
            if 'get-urls-from-client' in rule_id:

                method = finding.get('extra').get('metavars').get('$METHOD', {}).get('abstract_content',"")
                url_package = finding.get('extra').get('metavars').get('$URLPACKAGE', {}).get('abstract_content',"")
                service = finding.get('extra').get('metavars').get('$SERVICE', {}).get('abstract_content',"")

                pref1 = finding.get('extra').get('metavars').get('$PREF1', {}).get('abstract_content',"")
                pref2 = finding.get('extra').get('metavars').get('$PREF2', {}).get('abstract_content',"")
                pref3 = finding.get('extra').get('metavars').get('$PREF3', {}).get('abstract_content',"")
                pref4 = finding.get('extra').get('metavars').get('$PREF4', {}).get('abstract_content',"")
                pref5 = finding.get('extra').get('metavars').get('$PREF5', {}).get('abstract_content',"")

                if pref1 :
                    url_package = f"{pref1}.{url_package}"
                if pref2 :
                    url_package = f"{pref2}.{url_package}"
                if pref3 :
                    url_package = f"{pref3}.{url_package}"
                if pref4 :
                    url_package = f"{pref4}.{url_package}"
                if pref5 :
                    url_package = f"{pref5}.{url_package}"

                url = f"/{url_package}.{service}/{method}" 

                # make dict package.client => method => url

                if client not in ext_clients:
                    ext_clients[client] = {}

                if method in ext_clients[client]:
                    ext_clients[client][method]['url'] = url

    logger.info(f"clients scan processed {len(client_files)} and found {len(ext_clients)}")

    # finding usage

    pkg_files = find_all_pkg_files(f"{code_folder}/internal/pkg")

    semgrep_results_per_file = {}

    for file in pkg_files:
        semgrep_results_per_file[file] = []

    if pkg_files:

        result = subprocess.run(
            ["semgrep", "-f", "sg_rules/parse-clients.yaml", "--json", "--metrics=off"] + pkg_files,
            capture_output=True,
            text=True
        )

        semgrep_data = json.loads(result.stdout)

        logger.info(f"pkg scan found {len(semgrep_data['results'])} objects")

        for finding in semgrep_data['results']:
            finding_file = finding.get('path')
            semgrep_results_per_file[finding_file].append(finding)

    clients_in_service = {}

    clients_methods_in_service = {}

    clients_methods_count = 0

    for pkg_file in pkg_files:

        file = pkg_file.replace(code_folder,"")

        # package for file

        package = ""

        for finding in semgrep_results_per_file[pkg_file]:

            rule_id = finding.get('check_id',"").split('.')[-1]
                    
            if 'get-package-from-service' in rule_id:

                package = finding.get('extra').get('metavars').get('$PACKAGE', {}).get('abstract_content',"")
                break
        
        # looking for local client names

        for finding in semgrep_results_per_file[pkg_file]:

            rule_id = finding.get('check_id',"").split('.')[-1]
                    
            if 'get-clients-from-service' in rule_id:

                service_impl = finding.get('extra').get('metavars').get('$SERVICEIMPL', {}).get('abstract_content',"")
                local_client_name = finding.get('extra').get('metavars').get('$LOCALCLIENT', {}).get('abstract_content',"")
                client_name = finding.get('extra').get('metavars').get('$CLIENT', {}).get('abstract_content',"") 

                # make dict package => service_impl => local_client_name => clent_name

                if package not in clients_in_service :
                    clients_in_service[package] = {}

                if service_impl not in clients_in_service[package] :
                    clients_in_service[package][service_impl] = {}
                
                if local_client_name not in clients_in_service[package][service_impl]:
                    clients_in_service[package][service_impl][local_client_name] = client_name

            if 'get-client-usage-in-service' in rule_id:

                service_impl = finding.get('extra').get('metavars').get('$SERVICEIMPL', {}).get('abstract_content',"")
                local_method = finding.get('extra').get('metavars').get('$LOCALMETHOD', {}).get('abstract_content',"")
                local_client_name = finding.get('extra').get('metavars').get('$LOCALCLIENT', {}).get('abstract_content',"")
                client_method = finding.get('extra').get('metavars').get('$CLIENTMETHOD', {}).get('abstract_content',"") 

                line_int = finding.get('start',{}).get('line',0)

                # make dict package => service_impl => local_client_name => ext_client_name

                if package not in clients_methods_in_service :
                    clients_methods_in_service[package] = {}

                if service_impl not in clients_methods_in_service[package] :
                    clients_methods_in_service[package][service_impl] = {}

                if local_method not in clients_methods_in_service[package][service_impl]:
                    clients_methods_in_service[package][service_impl][local_method] = {}

                if local_client_name not in clients_methods_in_service[package][service_impl][local_method]:
                    clients_methods_in_service[package][service_impl][local_method][local_client_name] = {}

                clients_methods_in_service[package][service_impl][local_method][local_client_name][client_method] = {'file': file,
                                                                                                                     'line': line_int}
                clients_methods_count = clients_methods_count + 1

    logger.info(f"clients scan processed {len(pkg_files)} pkg files and found {clients_methods_count} client calls")

    client_objects = []

    # grub all shit together

    for package, service_impls in clients_methods_in_service.items():
        for service_impl, local_methods in service_impls.items():
            for local_method, local_clients in local_methods.items(): 
                for local_client, client_methods in local_clients.items():
                    for client_method, client_method_data in client_methods.items():

                        if package in clients_in_service \
                            and service_impl in clients_in_service[package] \
                            and local_client in clients_in_service[package][service_impl]:

                            ext_client_name = clients_in_service[package][service_impl][local_client]

                            if ext_client_name in ext_clients :

                                if client_method in ext_clients[ext_client_name]:
                    
                                    client_object = ClientObject(
                                        project_id=project_id,
                                        branch_id=branch_id,
                                        package=package,
                                        method=local_method,
                                        client_name=ext_client_name,
                                        client_url=ext_clients[ext_client_name][client_method]['url'],
                                        client_input=ext_clients[ext_client_name][client_method]['input'],
                                        client_output=ext_clients[ext_client_name][client_method]['output'],
                                        file=client_method_data['file'],
                                        line=client_method_data['line']
                                    )

                                    fields = get_client_fields(session, ext_clients[ext_client_name][client_method]['url'])

                                    for field in fields:
                                        client_object.score += field.score

                                    client_objects.append(client_object)
                                else:
                                    logger.info(f"not found {client_method} client_method in {ext_clients[ext_client_name].keys()}")
                            else:
                                logger.info(f"not found {ext_client_name} client in {ext_clients.keys()}")

    logger.info(f"proto scan found {len(ext_clients)} methods and {len(client_objects)} client calls")
                                    
    return client_objects, 'scanned'



####################################
##  Ext Tf objects               ###
####################################     

def find_all_tf_files(root_dir):
    tf_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('main.tf') :
                tf_files.append(os.path.join(root, file))
    return tf_files


def run_tf_scan(project_path, project_id, branch_id, branch_commit):

    # Determine the local path for the clone
    project_local_path = f"{str(project_id)}/{str(branch_id)}/{branch_commit}"

    code_folder = f"code/{project_local_path}"

    tf_files = find_all_tf_files(f"{code_folder}")

    semgrep_results_per_file = {}

    for file in tf_files:
        semgrep_results_per_file[file] = []

    if tf_files:

        result = subprocess.run(
            ["semgrep", "-f", "sg_rules/parse-tf.yaml", "--json", "--metrics=off"] + tf_files,
            capture_output=True,
            text=True
        )

        semgrep_data = json.loads(result.stdout)

        logger.info(f"tf scan found {len(semgrep_data['results'])} objects")

        for finding in semgrep_data['results']:
            finding_file = finding.get('path')
            semgrep_results_per_file[finding_file].append(finding)


    tf_vms = {}

    for tf_file in tf_files:

        file = tf_file.replace(code_folder,"")
        
        for finding in semgrep_results_per_file[tf_file]:

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

            vm_uniq = f"{file} - {vm_name}"

            if vm_uniq not in tf_vms:
                tf_vms[vm_uniq] = {'vm_name': vm_name, 'file': file, 'line': 0}

            if vm_domain :
                tf_vms[vm_uniq]['vm_domain'] = vm_domain

            if vm_template :
                tf_vms[vm_uniq]['vm_template'] = vm_template

            if vm_pool :
                tf_vms[vm_uniq]['vm_pool'] = vm_pool

            if vm_desc :
                tf_vms[vm_uniq]['vm_desc'] = vm_desc

            if vm_server_cluster_name :
                tf_vms[vm_uniq]['vm_server_cluster_name'] = vm_server_cluster_name

            if vm_server_role :
                tf_vms[vm_uniq]['vm_server_role'] = vm_server_role

            if vm_server_owning_team :
                tf_vms[vm_uniq]['vm_server_owning_team'] = vm_server_owning_team

            if vm_server_maintaining_team :
                tf_vms[vm_uniq]['vm_server_maintaining_team'] = vm_server_maintaining_team

            if vm_prometheus_env :
                tf_vms[vm_uniq]['vm_prometheus_env'] = vm_prometheus_env

            if vlan_id :
                tf_vms[vm_uniq]['vlan_id'] = vlan_id

            if dc :
                tf_vms[vm_uniq]['dc'] = dc

            if 'get-vm-name' in rule_id:
                line_int = finding.get('start',{}).get('line',0)
                tf_vms[vm_uniq]['line'] = line_int

    tf_objects = []

    for vm_uniq, vm_data in tf_vms.items():

        tf_object = TfObject(
            project_id=project_id,
            branch_id=branch_id,
            vm_name=vm_data['vm_name'],
            file=vm_data['file']
        )

        for key, value in vm_data.items():
            setattr(tf_object, key, value)

        tf_objects.append(tf_object)


    logger.info(f"tf scan found {len(tf_objects)} tf vms")
                                    
    return tf_objects, 'scanned'


