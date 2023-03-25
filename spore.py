from loguru import logger
import boto3
from ssm_lambdas import call_lambda_tag_resource
from utils.config_loader import Config
from ssm_agent import get_closest_aws_region, get_location_from_ip, get_public_ip
from main import get_instance_information
import os

def env_vars_as_tags():
    import csv
    ENVIRONMENT_PATH='/etc/environment'
    tags = list()
    with open(ENVIRONMENT_PATH, 'r') as env_file:
        reader = csv.reader(env_file, delimiter="=")
        for line in reader:
            if line and 'Key' and line[0].upper() != 'PATH':
                tags.append(
                    {
                        'Key': line[0].replace('_', ' ').title(),
                        'Value': line[1].replace('"', '').replace(',',' ')
                    }
                )
    tags.append(
        {
            'Key': 'Instance Id',
            'Value': get_instance_information()['instance-id']
        }
    )
    tags.append(
        {
            'Key': 'Name',
            'Value': os.getenv('SITE_ID')
        }
    )
    logger.debug(f'{tags}')
    return tags

if __name__ == '__main__':
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

    session = session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region_name
    )
    tags = env_vars_as_tags()
    call_lambda_tag_resource(session, tags)

