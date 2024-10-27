import re
from logger import get_logger

logger = get_logger(__name__)

def score_field(service, object, object_type, field_name, field_type, score_rules):

    for rule in score_rules:

        if ( not rule.service_re or re.match(rule.service_re, service) or rule.service_re.lower() in service.lower()) \
          and ( not rule.object_re or re.match(rule.object_re, object) or rule.object_re.lower() in object.lower() ) \
          and ( not rule.object_type_re or re.match(rule.object_type_re, object_type) or rule.object_type_re.lower() in object_type.lower() ) \
          and ( not rule.field_re or re.match(rule.field_re, field_name) or rule.field_re.lower() in field_name.lower() ) \
          and ( not rule.field_type_re or re.match(rule.field_type_re, field_type) or rule.field_type_re.lower() in field_type.lower() ) :
            logger.info(f"Object {object}, field {field_name} scored as risky for {str(rule.risk_score)}")
            return rule.risk_score
    
    return 0 
