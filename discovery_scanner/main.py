import multiprocessing as mp
import time

from services.gl_service import (
    get_gitlab_projects_list, 
    get_gitlab_branches_by_project, 
    get_gitlab_mrs_by_project,
    clone_gitlab_project_code,
    get_gitlab_project_lang,
    get_gitlab_code_cache_size,
    get_cloned_projects,
    remove_cloned_branch,
    remove_cloned_project
)
from services.scan_service import (
    scan_branch,
    scan_mr
)
from services.db_service import (
    create_db_and_tables,
    get_db_session,
    update_project,
    upsert_project, 
    upsert_branch, 
    update_branch,
    upsert_mr,
    update_mr,
    get_branch
)
from datetime import datetime, timedelta
from logger import get_logger
from config import GITLAB_PROJECTS_PREFIX, MAX_WORKERS, CACHE_SIZE, set_auth

logger = get_logger(__name__)

def update_projects(update_branches_mrs_queue):

    session = get_db_session()

    first_time_run = True

    while True:

        for prefix in GITLAB_PROJECTS_PREFIX: 

            projects = get_gitlab_projects_list(prefix)

            for project_gl in projects:

                project_db, _ = upsert_project(session, project_gl)

                if first_time_run or project_db.processed_at is None or project_db.processed_at < project_db.updated_at :
                    update_branches_mrs_queue.put((project_gl,project_db))

                    project_db.processed_at = datetime.now()
                    update_project(session, project_db)     

        first_time_run = False

        time.sleep(300)


def update_branches_mrs(update_branches_mrs_queue,  pull_code_queue):

    session = get_db_session()

    while True:

        project_gl, project_db = update_branches_mrs_queue.get()

        branches = get_gitlab_branches_by_project(project_gl.id)

        for branch_gl in branches:
            is_main = (branch_gl.name == project_gl.default_branch)
            branch_db, _ = upsert_branch(session, branch_gl, project_db.id, project_db.full_path, is_main)

            if is_main and ( branch_db.processed_at is None or branch_db.processed_at < branch_db.updated_at ):
                pull_code_queue.put((branch_db,'main'))
                
        mrs_gl = get_gitlab_mrs_by_project(project_gl.id)

        for mr_gl in mrs_gl:

            source_branch = get_branch(session, project_db.id, mr_gl.source_branch)
            target_branch = get_branch(session, project_db.id, mr_gl.target_branch)

            if source_branch and target_branch:
                mr_db, _ = upsert_mr(session, mr_gl, project_db.id, project_db.full_path, source_branch, target_branch)

                if mr_db.state == 'opened' and mr_db.updated_at > datetime.now() - timedelta(days=1) and ( mr_db.processed_at is None or mr_db.processed_at < mr_db.updated_at ):
                    pull_code_queue.put((mr_db,'mr'))   


def pull_code(pull_code_queue, scan_mrs_queue, scan_mains_queue, projects_in_work):

    session = get_db_session()

    while True:

        current_size = get_gitlab_code_cache_size()

        if current_size > CACHE_SIZE:

            logger.info(f"Cache to big, no more clones until we dial with exist ones")
    
            time.sleep(300)
            continue 

        obj, obj_type = pull_code_queue.get()

        if obj_type == 'main':

            main_branch = obj

            lang = get_gitlab_project_lang(main_branch.project_path, main_branch.branch_name)

            if lang in ['go', 'tf']:

                clone_branch_res = clone_gitlab_project_code(main_branch.project_path, main_branch.branch_name, main_branch.project_id, main_branch.id, main_branch.commit)

                if clone_branch_res:

                    if obj.project_id not in projects_in_work:
                        project_in_work = {'mrs':{}, 'main': {}, 'last_update': datetime.now()}
                    else:
                        project_in_work = projects_in_work[obj.project_id].copy()

                    project_in_work['main'][main_branch.id] = 1
                    project_in_work['last_update'] = datetime.now()

                    projects_in_work[obj.project_id] = project_in_work

                    scan_mains_queue.put(main_branch)

                else:         
                    main_branch.processed_at = datetime.now()
                    update_branch(session, main_branch)
        
            else:         
                main_branch.processed_at = datetime.now()
                update_branch(session, main_branch)

        if obj_type == 'mr':

            mr = obj

            lang = get_gitlab_project_lang(mr.project_path, mr.source_branch)

            if lang in ['go', 'tf']:

                clone_source_branch_res = clone_gitlab_project_code(mr.project_path, mr.source_branch, mr.project_id, mr.source_branch_id, mr.source_branch_commit)
                clone_target_branch_res = clone_gitlab_project_code(mr.project_path, mr.target_branch, mr.project_id, mr.target_branch_id, mr.target_branch_commit)

                if clone_source_branch_res and clone_target_branch_res:

                    if mr.project_id not in projects_in_work:
                        project_in_work = {'mrs':{}, 'main': {}, 'last_update': datetime.now()}
                    else:
                        project_in_work = projects_in_work[obj.project_id].copy()

                    project_in_work['mrs'][mr.id] = 1
                    project_in_work['last_update'] = datetime.now()

                    projects_in_work[mr.project_id] = project_in_work

                    scan_mrs_queue.put(mr)

                else:
                    mr.processed_at = datetime.now()
                    update_mr(session, mr)

            else:
                mr.processed_at = datetime.now()
                update_mr(session, mr)

           
def scan_mains(scan_mains_queue, projects_in_work):

    session = get_db_session()

    while True:

        main_branch = scan_mains_queue.get()

        scan_branch(session, main_branch)

        if main_branch.project_id in projects_in_work:
            project_in_work = projects_in_work[main_branch.project_id].copy()
            project_in_work['main'].pop(main_branch.id, None)
            project_in_work['last_update'] = datetime.now()

            projects_in_work[main_branch.project_id] = project_in_work

        main_branch.processed_at = datetime.now()
        update_branch(session, main_branch)


def scan_mrs(scan_mrs_queue, projects_in_work):

    session = get_db_session()

    while True:

        mr = scan_mrs_queue.get()

        scan_mr(session, mr.project_id, mr.project_path, mr.mr_id,
            mr.source_branch, mr.source_branch_id, mr.source_branch_commit,
            mr.target_branch, mr.target_branch_id, mr.target_branch_commit)
        
        if mr.project_id in projects_in_work:
            project_in_work = projects_in_work[mr.project_id].copy()
            project_in_work['mrs'].pop(mr.id, None)
            project_in_work['last_update'] = datetime.now()

            projects_in_work[mr.project_id] = project_in_work

        # clean one time source code and artifacts, safe target code
        remove_cloned_branch(mr.project_id, mr.source_branch_id)

        mr.processed_at = datetime.now()
        update_mr(session, mr)          


def clean_cache(projects_in_work):

    while True:

        project_ids = get_cloned_projects()
        sorted_piw = dict(sorted(projects_in_work.copy().items(), key=lambda item: item[1]['last_update']))

        logger.info(f"Cleaning local cached code for {len(project_ids)} projects, {len(sorted_piw)} projects in work")

        for project_id in project_ids:

            if project_id in sorted_piw and len(sorted_piw[project_id]['main']) == 0 and len(sorted_piw[project_id]['mrs']) == 0 :

                logger.info(f"Project {project_id} code cache can be cleared")

                current_size = get_gitlab_code_cache_size()

                if current_size > (CACHE_SIZE / 3):   
                    remove_cloned_project(project_id)
                    projects_in_work.pop(project_id, None)
                else:                   
                    break  
        
        time.sleep(60)


def main():

    create_db_and_tables()

    set_auth()

    manager = mp.Manager()
    projects_in_work = manager.dict()

    update_branches_mrs_queue = mp.Queue()
    pull_code_queue = mp.Queue()
    scan_mrs_queue = mp.Queue()
    scan_mains_queue = mp.Queue()

    # load projects info
    update_projects_worker = mp.Process(target=update_projects, args=(update_branches_mrs_queue,))
    update_projects_worker.start()        

    # load branches and mrs 
    update_branches_mrs_worker = mp.Process(target=update_branches_mrs, args=(update_branches_mrs_queue, pull_code_queue, ))
    update_branches_mrs_worker.start()

    # pull code for scans
    pull_code_worker = mp.Process(target=pull_code, args=(pull_code_queue, scan_mrs_queue, scan_mains_queue, projects_in_work))
    pull_code_worker.start()
    
    # clear cache for allready scanned projects
    clean_cache_worker = mp.Process(target=clean_cache, args=(projects_in_work,))
    clean_cache_worker.start() 

    # scan workers
    for i in range(MAX_WORKERS):
        
        scan_mrs_worker = mp.Process(target=scan_mrs, args=(scan_mrs_queue, projects_in_work))
        scan_mrs_worker.start()

        scan_mains_worker = mp.Process(target=scan_mains, args=(scan_mains_queue, projects_in_work))
        scan_mains_worker.start()

    # wait for subprocesses and handle piw dict
    clean_cache_worker.join()


if __name__ == "__main__":

    logger.info("Starting application...")

    main()