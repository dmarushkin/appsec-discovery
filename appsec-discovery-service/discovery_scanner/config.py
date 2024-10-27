import os
import subprocess
from logger import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL") 
GITLAB_PRIVATE_TOKEN = os.getenv("GITLAB_PRIVATE_TOKEN") 
GITLAB_URL = os.getenv("GITLAB_URL")

GITLAB_PROJECTS_PREFIX = os.getenv("GITLAB_PROJECTS_PREFIX").split(",")

MAX_WORKERS = int(os.getenv("MAX_WORKERS"))
CACHE_SIZE = int(os.getenv("CACHE_SIZE_GB")) * 1024 * 1024 * 1024

MR_ALERTS = os.getenv("MR_ALERTS")

TG_ALERT_TOKEN = os.getenv("TG_ALERT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def set_auth():

    try:

        gitconf_obj = open("/root/.gitconfig", "w")
        gitconf_obj.write("[credential]\n        helper = store\n")
        gitconf_obj.close()

        gitcreds_obj = open("/root/.git-credentials", "w")
        gitcreds_obj.write(GITLAB_URL.replace('://', "://git:" + GITLAB_PRIVATE_TOKEN + "@") )
        gitcreds_obj.close()

        subprocess.run(["chmod", "600", "/root/.git-credentials"], check=True)

    except Exception as ex:
        logger.error(f"Error writing configs: {ex}")