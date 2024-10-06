import gitlab
from config import GITLAB_URL, GITLAB_PRIVATE_TOKEN
import subprocess
import os
import math
from logger import get_logger
from os import path, listdir, makedirs
from datetime import datetime

logger = get_logger(__name__)

# Initialize a GitLab object
gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_PRIVATE_TOKEN)

def get_gitlab_projects_list(search_prefix):

    logger.info(f"Fetching projects from GitLab for prefix {search_prefix}")

    projects = gl.projects.list(iterator=True, search_namespaces=True, search=search_prefix)

    filtered_projects = [proj for proj in projects if proj.path_with_namespace.startswith(search_prefix)]

    logger.info(f"Fetched {len(filtered_projects)} projects.")

    return filtered_projects

def get_gitlab_branches_by_project(project_id):
    """Fetch a list of branches for a given project ID from GitLab."""

    # logger.info(f"Fetching branches for project {project_id}...")

    project = gl.projects.get(project_id)
    branches = project.branches.list(all=True)

    # logger.info(f"Fetched {len(branches)} branches.")

    return branches

def get_gitlab_mrs_by_project(project_id):
    """Fetch a list of branches for a given project ID from GitLab."""

    # logger.info(f"Fetching branches for project {project_id}...")

    project = gl.projects.get(project_id)
    mrs = project.mergerequests.list(state='opened', order_by='updated_at', iterator=True)

    # logger.info(f"Fetched {len(mrs)} mrs for project id {project_id}.")

    return mrs

def add_gitlab_comment_to_mr(project_path, mr_id, comment):
    
    logger.info(f"Adding comment for project {project_path} and mr {mr_id} ")

    try:

        project = gl.projects.get(project_path)
        mr = project.mergerequests.get(mr_id)

        mr_comment = mr.notes.create({'body': comment})

        logger.info(f"mr_comment {mr_comment} created.")

        return mr_comment

    except Exception as e:
        logger.error(f"Failed to add {project_path}, mr {mr_id}: {e}")

        return False

def get_gitlab_code_cache_size():

    code_folder = "./code"
    reports_folder = "./scans"

    code_bytes = 0
    reports_bytes = 0 

    try:
        if path.isdir(code_folder) :
            # code_bytes = sum(d.stat().st_size for d in os.scandir(code_folder) if d.is_file())
            for local_path, dirs, files in os.walk(code_folder):
                for f in files:
                    fp = os.path.join(local_path, f)
                    code_bytes += os.path.getsize(fp)
        if path.isdir(reports_folder) :
            # reports_bytes = sum(d.stat().st_size for d in os.scandir(reports_folder) if d.is_file())
            for local_path, dirs, files in os.walk(reports_folder):
                for f in files:
                    fp = os.path.join(local_path, f)
                    reports_bytes += os.path.getsize(fp)
    except Exception as e:
        logger.error(f"Failed to get cache size: {e}")

    cache_bytes = code_bytes + reports_bytes
    
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    
    if cache_bytes:

        i = int(math.floor(math.log(cache_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(cache_bytes / p, 2)
    else:
        i = 0
        s = 0

    logger.info(f"Current cache size is {s} {size_name[i]}")

    return cache_bytes


def clone_gitlab_project_code(project_path, branch_name, project_id, branch_id, branch_commit):

    # Construct the clone URL using the GitLab project's path

    project_url = f"{GITLAB_URL}/{project_path}.git/"
   
    # Determine the local path for the clone
    project_local_path = f"./code/{str(project_id)}/{str(branch_id)}/{branch_commit}"

    # Check if code already exist
    if path.isdir(project_local_path) and listdir(path=project_local_path) :
        logger.info(f"Folder {project_local_path} already exists")
        return True

    # Clone the branch
    try:
        subprocess.run(["rm", "-rf", project_local_path], check=True)

        subprocess.run(["git", "clone", "--branch", branch_name, "--single-branch", project_url, project_local_path], check=True)

        if path.isdir(project_local_path) and listdir(path=project_local_path) :

            logger.info(f"Successfully cloned project {project_path}, branch {branch_name} to local path {project_local_path}")
            return True
        
        else:
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone {project_path}, branch {branch_name}: {e}")

        return False
    

def get_gitlab_project_lang(project_path, branch_name):

    lang = 'other'

    project = None

    file = None

    try:
        project = gl.projects.get(project_path)
    except gitlab.exceptions.GitlabGetError:
        logger.info(f"Detected lang for project {project_path} is {lang}")
        return lang

    if 'terraform' in project_path:

        lang = "tf"
        logger.info(f"Detected lang for project {project_path} is {lang}")

        return lang

    try:
        file = project.files.get(file_path='go.mod', ref=branch_name)
    except gitlab.exceptions.GitlabGetError:
        pass

    if file:
        lang = "go"
        logger.info(f"Detected lang for project {project_path} is {lang}")

        return lang
    
    try:
        file = project.files.get(file_path='package.json', ref=branch_name)
    except gitlab.exceptions.GitlabGetError:
        pass

    if file:
        lang = "js"
        logger.info(f"Detected lang for project {project_path} is {lang}")

        return lang
    
    return lang



def get_cloned_projects():

    projects_ids = []

    projects_local_path = f"./code"

    if not path.exists(projects_local_path):
        makedirs(projects_local_path)

    projects_list = listdir(path=projects_local_path)

    projects_ids = [ int(id) for id in projects_list ]

    return projects_ids

def remove_cloned_branch(project_id, branch_id):

    # Determine the local path for the clone
    branch_code_path = f"./code/{str(project_id)}/{str(branch_id)}"
    branch_scans_path = f"./scans/{str(project_id)}/{str(branch_id)}"

    # delete branch
    try:
        subprocess.run(["rm", "-rf", branch_code_path], check=True)
        subprocess.run(["rm", "-rf", branch_scans_path], check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete {branch_code_path}: {e}")

    if path.isdir(branch_code_path) or path.isdir(branch_scans_path) :
        logger.error(f"Folder {branch_code_path} not deleted")
        return False
    else:
        logger.info(f"Folder {branch_code_path} deleted")
        return True


def remove_cloned_project(project_id):

    # Determine the local path for the clone
    project_code_path = f"./code/{str(project_id)}"

    project_scans_path = f"./scans/{str(project_id)}"

    # delete branch
    try:
        subprocess.run(["rm", "-rf", project_code_path], check=True)
        subprocess.run(["rm", "-rf", project_scans_path], check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete {project_code_path}: {e}")

    if path.isdir(project_code_path) :
        logger.error(f"Folder {project_code_path} not deleted")
        return False
    else:
        logger.info(f"Folder {project_code_path} deleted")
        return True
   
