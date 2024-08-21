import requests
import json
from logger import get_logger

from config import MM_ALERT_TOKEN, MM_ALERT_URL, TG_ALERT_TOKEN, TG_CHAT_ID, GITLAB_URL

logger = get_logger(__name__)

def render_and_send_alert(project, branch, mr_id, crit_objects):

    title = f"New sensitive objects in project {project}"

    message = f'Branch: {branch}\nMR: {GITLAB_URL}/{project}/-/merge_requests/{mr_id}/diffs\n'

    if crit_objects['table_objs']:

        message += '\nTable fields:\n'

        for table_obj in crit_objects['table_objs'].values():
            message += f'  {table_obj.table_name}.{table_obj.field} scored as risky for {table_obj.score}\n'


    if crit_objects['proto_objs']:

        message += '\nProto fields:\n'

        for proto_obj in crit_objects['proto_objs'].values():
            message += f'  {proto_obj.service}.{proto_obj.method}.{proto_obj.message}.{proto_obj.field} scored as risky for {proto_obj.score}\n'

    if crit_objects['client_objs']:

        message += '\nClient calls:\n'

        for client_obj in crit_objects['proto_objs'].values():
            message += f'  {client_obj.package}{client_obj.method} calls {client_obj.url} scored as risky for {client_obj.score}\n'

    if MM_ALERT_TOKEN and MM_ALERT_URL:
        
        send_mm_alert(title, message)

        logger.info(f"Alert for {project}, mr {mr_id} sent to mm")

        return True

    if TG_ALERT_TOKEN and TG_CHAT_ID:
        send_tg_alert(title, message)
        logger.info(f"Alert for {project}, mr {mr_id} sent to tg")

        return True
    
    logger.error(f"Alert for {project}, mr {mr_id} does not sent, {MM_ALERT_TOKEN} {MM_ALERT_URL}")

def send_mm_alert(alert_title, alert_text):

    # Payload for the POST request
    payload = {
        "description": alert_text,
        "message": alert_title,
        "details": {
            "responsible_team": "appsec_team",
            "severity": "low",
            "channel": "appsec-duty"
        },
        "priority": "P4",
        "responders": [{"name": "appsec_team", "type": "team"}]
    }

    # Headers for the POST request
    headers = {
        "authorization": f"AuthKey {MM_ALERT_TOKEN}",
        "Content-Type": "application/json"
    }

    # Making the POST request
    response = requests.post(MM_ALERT_URL, data=json.dumps(payload), headers=headers)

    # Checking the response
    if response.status_code == 200:
        print("Alert created successfully")
    else:
        print(f"Failed to create alert: {response.status_code}")
        print(response.text)


def send_tg_alert(alert_title, alert_text):

    text = f"{alert_title}\n{alert_text}"

    url = f"https://api.telegram.org/bot{TG_ALERT_TOKEN}/sendMessage"

    payload = {
        'chat_id': TG_CHAT_ID,
        'text': text
    }

    response = requests.post(url, json=payload)
    
    # Checking the response
    if response.status_code == 200:
        print("Alert created successfully")
    else:
        print(f"Failed to create alert: {response.status_code}")
        print(response.text)




