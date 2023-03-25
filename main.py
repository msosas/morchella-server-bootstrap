import boto3
from loguru import logger

def get_node_serial_number():
    from dmidecode import DMIDecode
    dmi = DMIDecode()
    logger.debug(dmi.serial_number())
    return dmi.serial_number()

def get_linux_distribution():
    import csv
    RELEASE_DATA = {}
    with open("/etc/os-release") as f:
        reader = csv.reader(f, delimiter="=")
        for row in reader:
            if row:
                RELEASE_DATA[row[0]] = row[1]
    return RELEASE_DATA


def get_model():
    from dmidecode import DMIDecode
    class ExtendedDMI(DMIDecode):
        def system_family(self):
            return self.get("System")[0].get("Family", self.default)
    dmi = ExtendedDMI()
    return dmi.system_family()

def create_aws_session(aws_access_key_id, aws_secret_access_key, aws_region_name='ap-southeast-2'):
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region_name
    )
    return session

def get_instance_information():
    import json
    from subprocess import run
    AGENT_CLI_PATH = '/snap/bin/amazon-ssm-agent.ssm-cli'

    response = run([
        AGENT_CLI_PATH,
        'get-instance-information',
    ], capture_output=True)
    logger.debug(json.loads(response.stdout.decode('utf8')))
    return json.loads(response.stdout.decode('utf8'))

def deactivate_cronjob(cronjob='/etc/cron.d/morchella'):
    cronjob_content = ""
    with open(cronjob, 'r') as cron_job_file:
        if cron_job_file.read() != '':
            for line in cron_job_file:
                print(line)
                cronjob_content = cronjob_content + (f'#{line}\n')
        else:
            logger.warning(f'Cron task is not defined')
    with open(cronjob, 'w') as cron_job_file:
        cron_job_file.write(cronjob_content)



def main():
    from ssm_agent import stop_agent, start_agent, get_customer_name, get_public_ip, get_closest_aws_region, get_location_from_ip
    from ssm_lambdas import call_lambda_ssm_register_node, call_lambda_tag_resource
    from utils.config_loader import Config
    from config import Config as Slack_Config
    from slacker import Slacker

    # Start Configuration
    CONFIG_PATH = '/opt/morchella/config.ini'
    config = Config(CONFIG_PATH)

    public_ip = get_public_ip()
    latitude, longitude = get_location_from_ip(public_ip)
    aws_credentials = config.get_section('CREDENTIALS')
    aws_access_key_id = aws_credentials['AWS_ACCESS_KEY_ID']
    aws_secret_access_key = aws_credentials['AWS_SECRET_ACCESS_KEY']
    if 'AWS_REGION' in aws_credentials.keys():
        aws_region_name = aws_credentials['AWS_REGION']
    else:
        aws_region_name = f'{get_closest_aws_region(latitude, longitude)}'
    morchella_config = config.get_section('morchella')
    node_auto_register = morchella_config['AUTO_REGISTER'] if morchella_config['AUTO_REGISTER'] == '-y' else ''
    slack_web_hook = config.get_section('SLACK')['SLACK_WEB_HOOK']
    slack_channel = config.get_section('SLACK')['SLACK_CHANNEL']
    slack_config = Slack_Config(slack_web_hook=slack_web_hook, slack_channel=slack_channel)
    slacker = Slacker(slack_config)
    # End of config

    activation_id = None
    request_msg_sent = False
    aws_session = create_aws_session(aws_access_key_id, aws_secret_access_key, aws_region_name)
    node_registration_info = None
    
    stop_agent()
    while not activation_id:
        if not request_msg_sent:
            message = {
                'username': 'morchella',
                'message': f'New  server: *{get_node_serial_number()}*\nPlease, upload the json config file to S3 using /morchella_new'
            }
            slacker.send_message(
                message=message
            )
            request_msg_sent = True
        node_registration_info = call_lambda_ssm_register_node(aws_session, get_node_serial_number(), node_auto_register, aws_region_name)
        if node_registration_info:
            activation_id = node_registration_info['activation_id']
            node_metadata = node_registration_info['node_metadata']
    logger.info(f'ActivationId: {activation_id}')
    
    start_agent()
    instance_id = get_instance_information()['instance-id']
    server_model = get_model()
    release_data = get_linux_distribution()
    tags = [
        {
            'Key': 'Instance Id',
            'Value': instance_id
        },
        {
            'Key': 'IP',
            'Value': public_ip
        },
        {
            'Key': 'Model',
            'Value': server_model
        },
        {
            'Key': 'System',
            'Value': f'{ release_data["NAME"] } { release_data["VERSION_ID"] }'
        }
    ]
    node_metadata_msg = ''
    for k, v in node_metadata.items():
        node_metadata_msg += f'- {k}="{v}"\n'
    message = {
        'username': 'morchella',
        'message': f'*{get_node_serial_number()}* has been registered to AWS SSM with the following details:\n- Instance_ID:{instance_id}\n{node_metadata_msg}'
    }
    slacker.send_message(
        message=message
    )

    call_lambda_tag_resource(aws_session, tags)
    deactivate_cronjob()
    logger.success(f'Server successfully commissioned')

if __name__ == '__main__':
    logger.add("/opt/morchella/morchella.log", rotation="500 MB")
    main()