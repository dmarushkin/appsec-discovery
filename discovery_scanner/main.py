import multiprocessing as mp
import time

from services.gl_service import (
    get_gitlab_projects_list, 
    get_gitlab_branches_by_project, 
    get_gitlab_mrs_by_project,
    clone_gitlab_project_code,
    get_gitlab_project_lang,
    get_cloned_projects,
    remove_cloned_project
)
from services.scan_service import (
    scan_branch,
    scan_mr
)
from services.db_service import (
    create_db_and_tables,
    get_db_session,
    get_project,
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
from config import GITLAB_PROJECTS_PREFIX, MAX_WORKERS

logger = get_logger(__name__)

def update_projects(update_branches_mrs_queue):

    session = get_db_session()

    while True:

        for prefix in GITLAB_PROJECTS_PREFIX: 

            projects = get_gitlab_projects_list(prefix)

            for project_gl in projects:

                project_db, _ = upsert_project(session, project_gl)

                if project_db.processed_at is None or project_db.processed_at < project_db.updated_at  :
                    update_branches_mrs_queue.put((project_gl,project_db))

        time.sleep(300)


def update_branches_mrs(update_branches_mrs_queue,  pull_code_queue):

    session = get_db_session()

    while True:
        
        main_branch = None
        main_branch_in_mrs = False

        to_scan_count = 0

        project_gl, project_db = update_branches_mrs_queue.get()
    
        branches = get_gitlab_branches_by_project(project_gl.id)

        for branch_gl in branches:
            is_main = (branch_gl.name == project_gl.default_branch)
            branch_db, _ = upsert_branch(session, branch_gl, project_db.id, project_db.full_path, is_main)

            if is_main and ( branch_db.processed_at is None or branch_db.processed_at < branch_db.updated_at ):
                main_branch = branch_db
        
        mrs_gl = get_gitlab_mrs_by_project(project_gl.id)

        for mr_gl in mrs_gl:

            source_branch = get_branch(session, project_db.id, mr_gl.source_branch)
            target_branch = get_branch(session, project_db.id, mr_gl.target_branch)

            if source_branch and target_branch:
                mr_db, _ = upsert_mr(session, mr_gl, project_db.id, project_db.full_path, source_branch, target_branch)

                if mr_db.state == 'opened' and mr_db.updated_at > datetime.now() - timedelta(days=1) and ( mr_db.processed_at is None or mr_db.processed_at < mr_db.updated_at ):
                    pull_code_queue.put((mr_db,'mr'))
                    to_scan_count += 1

                    if mr_gl.target_branch == project_gl.default_branch :
                        main_branch_in_mrs = True

        if main_branch and not main_branch_in_mrs :
            pull_code_queue.put((main_branch,'main'))
            to_scan_count += 1

        if to_scan_count == 0 :
            project_db.processed_at = datetime.now()
            update_project(session, project_db)     


def pull_code(pull_code_queue, scan_mrs_queue, scan_mains_queue):

    session = get_db_session()

    while True:

        # limit storage usage
        cloned_projects = get_cloned_projects()
        if len(cloned_projects) > MAX_WORKERS:
            time.sleep(30)
            continue

        obj, obj_type = pull_code_queue.get()

        if obj_type == 'main':

            main_branch = obj

            lang = get_gitlab_project_lang(main_branch.project_path, main_branch.branch_name)

            if lang in ['go', 'tf']:

                clone_branch_res = clone_gitlab_project_code(main_branch.project_path, main_branch.branch_name, main_branch.project_id, main_branch.id, main_branch.commit)

                if clone_branch_res:
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
                    scan_mrs_queue.put(mr)
                else:
                    mr.processed_at = datetime.now()
                    update_mr(session, mr)

            else:
                mr.processed_at = datetime.now()
                update_mr(session, mr)

           
def scan_mains(scan_mains_queue):

    session = get_db_session()

    while True:

        main_branch = scan_mains_queue.get()

        scan_branch(session, main_branch)

        main_branch.processed_at = datetime.now()
        update_branch(session, main_branch)


def scan_mrs(scan_mrs_queue):

    session = get_db_session()

    while True:

        mr = scan_mrs_queue.get()
        
        target_branch = get_branch(session, mr.project_id, mr.target_branch)

        if target_branch.is_main and (target_branch.processed_at is None or target_branch.processed_at < target_branch.updated_at) :
            scan_branch(session, target_branch)

            target_branch.processed_at = datetime.now()
            update_branch(session, target_branch)

        scan_mr(session, mr.project_id, mr.project_path, mr.mr_id,
            mr.source_branch, mr.source_branch_id, mr.source_branch_commit,
            mr.target_branch, mr.target_branch_id, mr.target_branch_commit)

        mr.processed_at = datetime.now()
        update_mr(session, mr)       


def remove_code():

    session = get_db_session()

    while True:

        project_ids = get_cloned_projects()

        for project_id in project_ids:

            project = get_project(session, project_id)

            if project.processed_at and project.processed_at > project.updated_at:

                remove_cloned_project(project_id)

        time.sleep(3000)



def main():

    create_db_and_tables()


    update_branches_mrs_queue = mp.Queue()
    pull_code_queue = mp.Queue()
    scan_mrs_queue = mp.Queue()
    scan_mains_queue = mp.Queue()

    # load projects info

    update_projects_worker = mp.Process(target=update_projects, args=(update_branches_mrs_queue,))
    update_projects_worker.start()        

    update_branches_mrs_worker = mp.Process(target=update_branches_mrs, args=(update_branches_mrs_queue, pull_code_queue))
    update_branches_mrs_worker.start()

    
    # 5 instanses for each worker

    for i in range(MAX_WORKERS):

        # pull code for scans

        pull_code_worker = mp.Process(target=pull_code, args=(pull_code_queue, scan_mrs_queue, scan_mains_queue))
        pull_code_worker.start()

        # scan code
        
        scan_mrs_worker = mp.Process(target=scan_mrs, args=(scan_mrs_queue,))
        scan_mrs_worker.start()


        scan_mains_worker = mp.Process(target=scan_mains, args=(scan_mains_queue,))
        scan_mains_worker.start()


if __name__ == "__main__":

    logger.info("Starting application...")

    main()