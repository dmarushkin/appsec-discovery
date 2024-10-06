from sqlmodel import create_engine, SQLModel, Session, select
from models import Project, Branch, Scan, MR, TableObject, ProtoObject, ClientObject, TfObject, ScoreRule # , , ProtoObject, ClientCallObject
from datetime import datetime, timezone, timedelta
from logger import get_logger
from config import DATABASE_URL
import time

logger = get_logger(__name__)

engine = create_engine(DATABASE_URL)

def create_db_and_tables():

    # wait db warming up
    time.sleep(15)

    SQLModel.metadata.create_all(engine)


def get_db_session():
    engine = create_engine(DATABASE_URL)
    session = Session(engine)
    return session


def upsert_project(session, project_gl):

    local_project = Project(
        project_name=project_gl.name,
        full_path=project_gl.path_with_namespace,
        description=project_gl.description,
        visibility=project_gl.visibility,
        default_branch=project_gl.default_branch,
        created_at=datetime.strptime(project_gl.created_at, "%Y-%m-%dT%H:%M:%S.%fZ"),
        updated_at=datetime.strptime(project_gl.last_activity_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    )

    with session:
        statement = select(Project).where(Project.project_name == local_project.project_name)
        existing_project = session.exec(statement).first()

        if existing_project:
            if existing_project.updated_at < local_project.updated_at:
                logger.info(f"Updating existing project: {existing_project.full_path}")
                for key, value in local_project.model_dump(exclude_unset=True).items():
                    setattr(existing_project, key, value)
                result = 'updated'
            else:
                result = 'checked'
        else:
            logger.info(f"Inserting new project: {local_project.full_path}")
            existing_project = local_project
            session.add(existing_project)
            result = 'inserted'

        session.commit()
        session.refresh(existing_project)

        return existing_project, result

def update_project(session, project: Project):
    
    with session:
        statement = select(Project).where(Project.id == project.id)
        existing_project = session.exec(statement).first()

        # logger.info(f"Updating existing project: {existing_project.full_path}, p_id: {project.id}")
        for key, value in project.model_dump(exclude_unset=True).items():
            setattr(existing_project, key, value)
        result = 'updated'

        session.commit()
        session.refresh(existing_project)

        return existing_project, result

def get_project(session, project_id):

    with session:
        statement = select(Project).where(Project.id == project_id)
        existing_project = session.exec(statement).first()
        
        return existing_project

def get_projects(session):

    with session:
        projects = session.query(Project).all()
        logger.info(f"Load {len(projects)} from db")

        return projects
    
def upsert_branch(session, branch_gl, project_id, project_path, is_main):

    local_branch = Branch(
        branch_name=branch_gl.name,
        is_main=is_main,
        created_at=datetime.strptime(branch_gl.commit['committed_date'], "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=timezone.utc).replace(tzinfo=None),
        commit=branch_gl.commit['id'],
        updated_at=datetime.strptime(branch_gl.commit['committed_date'], "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=timezone.utc).replace(tzinfo=None),
        project_id=project_id,
        project_path=project_path
    )
    
    with session:
        statement = select(Branch).where(Branch.branch_name == local_branch.branch_name, Branch.project_id == local_branch.project_id)
        existing_branch = session.exec(statement).first()

        if existing_branch:
            if existing_branch.updated_at < local_branch.updated_at :
                logger.info(f"Updating existing branch: {existing_branch.branch_name}, p_id: {local_branch.project_id}")
                for key, value in local_branch.model_dump(exclude_unset=True).items():
                    setattr(existing_branch, key, value)
                result = 'updated'
            else:
                result = 'checked'
        else:
            logger.info(f"Inserting new branch: {local_branch.branch_name}")
            existing_branch = local_branch
            session.add(existing_branch)
            result = 'inserted'

        session.commit()
        session.refresh(existing_branch)

        return existing_branch, result
    
    
def update_branch(session, branch: Branch):
    
    with session:
        statement = select(Branch).where(Branch.id == branch.id)
        existing_branch = session.exec(statement).first()

        logger.info(f"Updating existing branch: {existing_branch.branch_name}, p_id: {branch.project_id}")
        for key, value in branch.model_dump(exclude_unset=True).items():
            setattr(existing_branch, key, value)
        result = 'updated'

        session.commit()
        session.refresh(existing_branch)

        return existing_branch, result

def get_branch(session, project_id, branch_name):

    with session:
        statement = select(Branch).where(Branch.branch_name == branch_name, Branch.project_id == project_id)
        existing_branch = session.exec(statement).first()
        
        return existing_branch

def get_active_branches(session, project_id):

    with session:
        statement = select(Branch).where(
            Branch.project_id == project_id
        )

        branches = session.exec(statement).all()
        active_branches =  [ branch for branch in branches if ( branch.processed_at is None or branch.processed_at < branch.updated_at ) and branch.updated_at > datetime.now() - timedelta(days=1)]

        return active_branches 

def upsert_mr(session, mr_gl, project_id, project_path, source_branch, target_branch):

    local_mr = MR(
        mr_id=mr_gl.iid,
        project_id=project_id,
        project_path=project_path,
        source_branch_id=source_branch.id,
        source_branch=source_branch.branch_name,
        source_branch_commit=source_branch.commit,
        target_branch_id=target_branch.id,
        target_branch=target_branch.branch_name,
        target_branch_commit=target_branch.commit,
        state=mr_gl.state,
        title=mr_gl.title,
        description=mr_gl.description,
        created_at=datetime.strptime(mr_gl.created_at, "%Y-%m-%dT%H:%M:%S.%fZ"),
        updated_at=datetime.strptime(mr_gl.updated_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    )

    with session:
        statement = select(MR).where(
            MR.project_id == local_mr.project_id,
            MR.mr_id == local_mr.mr_id)
        
        existing_mr = session.exec(statement).first()

        if existing_mr:
            if existing_mr.updated_at < local_mr.updated_at:
                logger.info(f"Updating existing mr: {existing_mr.mr_id}, p_id: {local_mr.project_id}")
                for key, value in existing_mr.model_dump(exclude_unset=True).items():
                    setattr(existing_mr, key, value)
                result = 'updated'
            else:
                result = 'checked'
        else:
            logger.info(f"Inserting new mr: {local_mr.mr_id}, p_id: {local_mr.project_id}")
            existing_mr = local_mr
            session.add(existing_mr)
            result = 'inserted'

        session.commit()
        session.refresh(existing_mr)

        return existing_mr, result

def update_mr(session, mr: MR):
    
    with session:
        statement = select(MR).where(MR.id == mr.id)
        existing_mr = session.exec(statement).first()

        logger.info(f"Updating existing branch: {existing_mr.mr_id}, p_id: {existing_mr.project_id}")
        for key, value in mr.model_dump(exclude_unset=True).items():
            setattr(existing_mr, key, value)
        result = 'updated'

        session.commit()
        session.refresh(existing_mr)

        return existing_mr, result

def get_active_mrs(session, project_id):

    with session:
        statement = select(MR).where(
            MR.project_id == project_id
        )

        mrs = session.exec(statement).all()
        active_mrs =  [ mr for mr in mrs if (mr.processed_at is None or mr.processed_at < mr.updated_at ) and mr.updated_at > datetime.now() - timedelta(days=1) ]

        return active_mrs 


def insert_scan(session, local_scan):

    with session:

        logger.info(f"Inserting new scan: {local_scan.scanner}")

        # Create a new branch record, considering is_main
        session.add(local_scan)
        session.commit()
        session.refresh(local_scan)
        return local_scan

def get_scan(session, scanner, rules_version, project_id, branch_id, branch_commit):
    
    with session:
        statement = select(Scan).where(
            Scan.scanner == scanner, 
            Scan.rules_version == rules_version, 
            Scan.project_id == project_id, 
            Scan.branch_id == branch_id, 
            Scan.branch_commit == branch_commit
        )
        
        existing_scan = session.exec(statement).first()
        return existing_scan 
    

def upsert_table_obj(session, local_table_obj: TableObject):

    updated_at = datetime.now()

    with session:

        statement = select(TableObject).where(
            TableObject.project_id == local_table_obj.project_id, 
            TableObject.branch_id == local_table_obj.branch_id, 
            TableObject.table_name == local_table_obj.table_name,
            TableObject.field == local_table_obj.field)
        
        existing_table = session.exec(statement).first()

        if existing_table:
            
            existing_table.updated_at = updated_at
            existing_table.file = local_table_obj.file
            existing_table.line = local_table_obj.line

            result = 'updated'

        else:

            existing_table = local_table_obj
            existing_table.updated_at = updated_at
            existing_table.created_at = updated_at

            session.add(existing_table)

            result = 'inserted'

        session.commit()
        session.refresh(existing_table)

        return existing_table, result


def upsert_proto_obj(session, local_proto_obj: ProtoObject):

    updated_at = datetime.now()

    with session:

        statement = select(ProtoObject).where(
            ProtoObject.project_id == local_proto_obj.project_id, 
            ProtoObject.branch_id == local_proto_obj.branch_id, 
            ProtoObject.url == local_proto_obj.url,
            ProtoObject.message == local_proto_obj.message,
            ProtoObject.field == local_proto_obj.field)
        
        existing_proto = session.exec(statement).first()

        if existing_proto:
            
            existing_proto.updated_at = updated_at
            existing_proto.file = local_proto_obj.file
            existing_proto.line = local_proto_obj.line
            existing_proto.type = local_proto_obj.type

            result = 'updated'

        else:

            existing_proto = local_proto_obj
            existing_proto.updated_at = updated_at
            existing_proto.created_at = updated_at

            session.add(existing_proto)

            result = 'inserted'

        session.commit()
        session.refresh(existing_proto)

        return existing_proto, result
    


def upsert_client_obj(session, local_client_obj: ClientObject):

    updated_at = datetime.now()

    with session:

        statement = select(ClientObject).where(
            ClientObject.project_id == local_client_obj.project_id, 
            ClientObject.branch_id == local_client_obj.branch_id, 
            ClientObject.package == local_client_obj.package,
            ClientObject.method == local_client_obj.method,
            ClientObject.client_name == local_client_obj.client_name,
            ClientObject.client_url == local_client_obj.client_url)
        
        existing_client = session.exec(statement).first()

        if existing_client:
            
            existing_client.updated_at = updated_at
            existing_client.file = local_client_obj.file
            existing_client.line = local_client_obj.line
            existing_client.client_input = local_client_obj.client_input
            existing_client.client_output = local_client_obj.client_output

            result = 'updated'

        else:

            existing_client = local_client_obj
            existing_client.updated_at = updated_at
            existing_client.created_at = updated_at

            session.add(existing_client)

            result = 'inserted'

        session.commit()
        session.refresh(existing_client)

        return existing_client, result
    
def get_client_fields(session, client_url):

    with session:
        statement = select(ProtoObject).where(
            ProtoObject.url == client_url
        )

        client_fields = session.exec(statement).all()
       
        scored_fields =  [ field for field in client_fields if field.score > 0 ]

        return scored_fields 


def get_score_rules(session):

    with session:
        rules = session.query(ScoreRule).all()
        logger.info(f"Load {len(rules)} score rules from db")

        return rules


def upsert_tf_obj(session, local_tf_obj: TfObject):

    updated_at = datetime.now()

    with session:

        statement = select(TfObject).where(
            TfObject.project_id == local_tf_obj.project_id, 
            TfObject.branch_id == local_tf_obj.branch_id, 
            TfObject.vm_name == local_tf_obj.vm_name,
            TfObject.vm_domain == local_tf_obj.vm_domain,
            TfObject.dc == local_tf_obj.dc)
        
        existing_tf = session.exec(statement).first()

        if existing_tf:

            logger.info(f"Updating existing tf vm: {existing_tf.vm_name}, vm_domain: {existing_tf.vm_domain}")
            for key, value in local_tf_obj.model_dump(exclude_unset=True).items():
                setattr(existing_tf, key, value)

            existing_tf.updated_at = updated_at

            result = 'updated'
            
        else:

            existing_tf = local_tf_obj
            existing_tf.updated_at = updated_at
            existing_tf.created_at = updated_at

            session.add(existing_tf)

            result = 'inserted'

        session.commit()
        session.refresh(existing_tf)

        return existing_tf, result