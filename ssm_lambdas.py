import json
from loguru import logger
import json

def log_lambda_response(lambda_response: str):
    lambda_payload = json.loads(lambda_response['Payload'].read())
    if 'ResponseMetadata' in lambda_payload.keys() and lambda_payload['ResponseMetadata']['HTTPStatusCode'] != 200 :
        logger.error(lambda_payload)
        raise SystemExit
    else:
        if 'errorMessage' in lambda_payload.keys():
            logger.error(lambda_payload)
            raise SystemExit
        else:
            logger.info(lambda_payload)
    return lambda_payload

def create_event(event_type='Morchella Server', data=None):
    from socket import gethostname
    from datetime import datetime
    
    currentDateAndTime = datetime.now()
    logger.debug(f'DATE AND TIME: {currentDateAndTime}')
    event = {
        'source': gethostname(),
        'detail-type': event_type,
        'event-date': str(currentDateAndTime),
        'detail': data,
    }
    return event

def configure_node_metadata(node_metadata: list):
    import csv
    logger.debug(node_metadata)
    ENVIRONMENT_PATH='/etc/environment'
    env_vars = dict()
    with open(ENVIRONMENT_PATH, 'r') as env_file:
        reader = csv.reader(env_file, delimiter="=")
        for line in reader:
            if line:
                env_vars[line[0].upper()] = line[1].replace('"', '')
    
    env_vars.update({k.upper():v for k,v in node_metadata.items()})
    logger.debug(env_vars)
    with open(ENVIRONMENT_PATH, 'w') as env_file:
        for key, value in env_vars.items():
            env_file.write(f'{key}="{value}"\n')
    logger.success(f'Node metadata has been written')

def call_lambda_ssm_register_node(aws_session, serial_number, programatic='',aws_region='ap-southeast-2'):
    from subprocess import run
    import json
    logger.debug(f'Using AWS REGION = {aws_region}')
    activation_id = None
    AGENT_CLI_PATH = '/snap/amazon-ssm-agent/current/amazon-ssm-agent'
    command_result = None
    try:
        response = aws_session.client('lambda').invoke(FunctionName='morchella-register-node', Payload=json.dumps({ 'serial_number': serial_number }))       
        payload = log_lambda_response(response)
        activation_id = payload['ActivationId']
        command_result = run([AGENT_CLI_PATH, '-register', '-code',
            payload['ActivationCode'], '-id', activation_id, '-region', aws_region, programatic], capture_output=True, timeout=30)
        logger.debug(f'{command_result.stdout.decode("utf8")}')
        configure_node_metadata(payload['node_metadata'])  
    except Exception as e:
        logger.error(f'{e}')
    finally:
        if activation_id:
            call_lambda_delete_activation(aws_session, activation_id)
            if command_result:
                return {
                    'activation_id': activation_id,
                    'node_metadata': payload['node_metadata']
                }
                
            else:
                return None

def call_lambda_delete_activation(aws_session, activation_id: str):
    try:
        response = aws_session.client('lambda').invoke(FunctionName='morchella-delete-activation', Payload=json.dumps({ 'activation_id': activation_id }) )
        log_lambda_response(response)
        logger.info(f'Activation {activation_id} deleted')
        return response
    except Exception as e:
        logger.error(f'{e}')

def call_lambda_tag_resource(aws_session, tags: list):
    try:
        event = create_event(data={
            'tags': tags
        })
        logger.debug(f'EVENT: {json.dumps(event)}')
        client = aws_session.client('lambda')
        response = client.invoke(FunctionName='morchella-tag-resource', Payload=json.dumps(event))
        log_lambda_response(response)
    except Exception as e:
        logger.error(f'{e}')
