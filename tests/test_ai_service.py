from appsec_discovery.services import ScanService
import pytest

from huggingface_hub import snapshot_download
from huggingface_hub import hf_hub_download

import os
from pathlib import Path

from llama_cpp import Llama



def test_ai_service_config_load():

    test_folder = str(Path(__file__).resolve().parent)
    config_file = os.path.join(test_folder, "config_samples/ai_conf_llama.yaml")

    with open(config_file, 'r') as conf_file:
        scan_service_llama = ScanService(source_folder="some", conf_file=conf_file)

    score_config_llama = scan_service_llama.config

    assert score_config_llama.ai_params is not None

    assert score_config_llama.ai_params.model_id == "mradermacher/Llama-3.2-3B-Instruct-uncensored-GGUF"

    assert "security bot" in score_config_llama.ai_params.prompt

@pytest.mark.skip(reason="Only manual use")
def test_ai_service_update_model_in_cache_llama():

    test_folder = str(Path(__file__).resolve().parent)
    config_file = os.path.join(test_folder, "config_samples/ai_conf_llama_8b.yaml")

    with open(config_file, 'r') as conf_file:
        scan_service = ScanService(source_folder="some", conf_file=conf_file)

    hf_hub_download(repo_id=scan_service.config.ai_params.model_id, filename=scan_service.config.ai_params.gguf_file, cache_dir=scan_service.config.ai_params.model_folder)
    
    assert 1==1

@pytest.mark.skip(reason="Only manual use")
def test_ai_service_score_objects_llama():

    test_folder = str(Path(__file__).resolve().parent)
    config_file = os.path.join(test_folder, "config_samples/ai_conf_llama_8b.yaml")

    samples_folder = os.path.join(test_folder, "ai_samples/code_objects")

    with open(config_file, 'r') as conf_file:
        scan_service = ScanService(source_folder=samples_folder, conf_file=conf_file)
   
    score_config = scan_service.config

    scanned_objects = scan_service.scan_folder()

    assert score_config.ai_params is not None
    assert score_config.ai_params.model_id == "mradermacher/Llama-3.2-3B-Instruct-uncensored-GGUF"

    assert scanned_objects[1].fields["Input.User.email"].field_name == "Input.User.email"
    assert scanned_objects[1].fields["Input.User.email"].severity == "medium"  
    assert "llm" in scanned_objects[1].fields["Input.User.email"].tags 

@pytest.mark.skip(reason="Only manual use")
def test_ai_service_score_objects_test():

    test_folder = str(Path(__file__).resolve().parent)
    config_file = os.path.join(test_folder, "config_samples/ai_conf_llama_8b.yaml")

    samples_folder = os.path.join(test_folder, "ai_samples/code_objects")

    with open(config_file, 'r') as conf_file:
        scan_service = ScanService(source_folder=samples_folder, conf_file=conf_file)
   
    score_config = scan_service.config

    llm = Llama.from_pretrained(
        repo_id=score_config.ai_params.model_id,
        filename=score_config.ai_params.gguf_file,
        verbose=False,
        cache_dir=score_config.ai_params.model_folder
    )
    
    text = '''
    Object: User
    Field_names:
        id
        full_name,
        first_name,
        last_name,
        music_album,
        address,
        snils,
        inn,
        pan,
        tshirt_size
        password
        auth_token
        user.codeword
        pets_lover
        documet_number
    '''

    system_prompt = ''' You are security bot, for provided objects select only field names that contain personally identifiable information, passport or other person identification document numbers, finance or payment information, authentication and other sensitive data. '''

    question = '''
    For object: Client
    
    Field name: inn

    Can contain sensitive data? Answer only 'yes' or 'no',
    '''


    response = llm.create_chat_completion(
      messages = [
          {"role": "system", "content": system_prompt},
          {
              "role": "user",
              "content": question
          }
      ]
    )

    answer = response['choices'][0]["message"]["content"]

    assert 1==1

