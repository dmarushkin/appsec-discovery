import gitlab
from config import GITLAB_URL, GITLAB_PRIVATE_TOKEN
import subprocess
from logger import get_logger
from os import path, listdir, makedirs

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

    logger.info(f"Fetching branches for project {project_id}...")

    project = gl.projects.get(project_id)
    branches = project.branches.list(all=True)

    logger.info(f"Fetched {len(branches)} branches.")

    return branches

def get_gitlab_mrs_by_project(project_id):
    """Fetch a list of branches for a given project ID from GitLab."""

    logger.info(f"Fetching branches for project {project_id}...")

    project = gl.projects.get(project_id)
    mrs = project.mergerequests.list(state='opened', order_by='updated_at', iterator=True)

    logger.info(f"Fetched {len(mrs)} mrs for project id {project_id}.")

    return mrs

def clone_gitlab_project_code(project_path, branch_name, project_id, branch_id, branch_commit):

    # Construct the clone URL using the GitLab project's path

    project_url = f"{GITLAB_URL}/{project_path}.git/".replace("://", f"://git:{GITLAB_PRIVATE_TOKEN}@")
   
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


def remove_cloned_project(project_id):

    # Determine the local path for the clone
    project_local_path = f"./code/{str(project_id)}"

    # delete branch
    try:
        subprocess.run(["rm", "-rf", project_local_path], check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete {project_local_path}: {e}")

    if path.isdir(project_local_path) :
        logger.error(f"Folder {project_local_path} not deleted")
        return False
    else:
        logger.info(f"Folder {project_local_path} deleted")
        return True