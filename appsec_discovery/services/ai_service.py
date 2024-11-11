from llama_cpp import Llama
import json
import yaml
import re

from typing import List, Dict
import logging

from appsec_discovery.models import CodeObject, ExcludeScoring, AiParams

severities_int = {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'info': 1}
skip_ai = ['created_at', 'updated_at', 'deleted_at']

logger = logging.getLogger(__name__)

class AiService:

    def __init__(self, ai_params: AiParams, exclude_scoring: List[ExcludeScoring]):

        self.model_id = ai_params.model_id
        self.model_folder = ai_params.model_folder
        self.system_prompt = ai_params.prompt
        self.gguf_file = ai_params.gguf_file
        self.exclude_scoring = exclude_scoring
        

    def ai_score_objects(self, code_objects: List[CodeObject]) -> List[CodeObject]:

        scored_objects: List[CodeObject] = []

        try:

            llm = Llama.from_pretrained(
                repo_id=self.model_id,
                filename=self.gguf_file,
                verbose=False,
                cache_dir=self.model_folder
            )

            for object in code_objects:

                object_to_score: Dict[str: List[str]] = {'field_names': []}
                
                for field in object.fields.values() :

                    # no ai for already sensitive
                    if not field.severity \
                      and not ( field.field_name.split('.')[-1] in skip_ai \
                            or field.field_name.lower().endswith('id') \
                            or 'status' not in field.field_name.split('.')[-1].lower() ):
                        object_to_score['field_names'].append(field.field_name.split('.')[-1])
                
                object_text = f"object: {object.object_name}\n\n" + yaml.safe_dump(object_to_score)

                scored_list = []

                if object_to_score['field_names'] :
                
                    response = llm.create_chat_completion(
                        messages = [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": object_text },
                        ]
                    )

                    answer = response['choices'][0]["message"]["content"]

                    if '[' in answer and ']' in answer:

                        json_txt = "[" + answer.split('[')[1].split(']')[0] + "]"
                        scored_list = json.loads(json_txt)

                scored_fields = {}

                tag = "llm"
                severity = "medium"

                for field_name, field in object.fields.items():

                    if field.field_name.split('.')[-1] in scored_list:

                        excluded = False

                        for exclude in self.exclude_scoring:

                            if ( exclude.file or exclude.parser or exclude.object_name or exclude.object_type or exclude.prop_name 
                                    or exclude.field_name or exclude.field_type or exclude.tag or exclude.keyword ) \
                                and (exclude.parser is None or exclude.parser.lower() == object.parser.lower()) \
                                and (exclude.file is None or re.match(exclude.file, object.file) or exclude.file.lower() in object.file.lower()) \
                                and (exclude.object_name is None or re.match(exclude.object_name, object.object_name) or exclude.object_name.lower() in object.object_name.lower()) \
                                and (exclude.object_type is None or re.match(exclude.object_type, object.object_type) or exclude.object_type.lower() in object.object_type.lower()) \
                                and (exclude.prop_name is None ) \
                                and (exclude.field_name is None or re.match(exclude.field_name, field.field_name) or exclude.field_name.lower() in field.field_name.lower()) \
                                and (exclude.field_type is None or re.match(exclude.field_type, field.field_type) or exclude.field_type.lower() in field.field_type.lower()) \
                                and (exclude.tag is None or exclude.tag == tag ) \
                                and (exclude.keyword is None ) :
                                
                                excluded = True

                        if not excluded :

                            if not field.severity:
                                field.severity = severity
                                field.tags = [tag]
                            else:
                                if tag not in field.tags:
                                    field.tags.append(tag)

                                if severities_int[severity] > severities_int[field.severity]:
                                    field.severity = severity

                            if not object.severity:
                                object.severity = severity
                                object.tags = [tag]
                            else:
                                if tag not in object.tags:
                                    object.tags.append(tag)

                                if severities_int[severity] > severities_int[object.severity]:
                                    object.severity = severity

                    scored_fields[field_name] = field
                
                object.fields = scored_fields

                scored_objects.append(object)

        except Exception as ex:
            logger.error(f"Error while ai scoring: {ex}")

        # Check that all processed
        if len(scored_objects) == len(code_objects):
            return scored_objects
        
        else:
            return code_objects
