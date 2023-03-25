import os
from loguru import logger
import requests
import math

def get_customer_name():
    customer = os.getenv('CUSTOMER')
    if customer:
        return customer
    else:
        return None

def stop_agent(agent_name='snap.amazon-ssm-agent.amazon-ssm-agent.service'):    
    import time
    try:
        os.popen(f"sudo systemctl stop { agent_name }")
        while checkServiceStatus('active'):
            time.sleep(5)
        logger.success("SSM Agent stopped successfully...")
        return True        
    except OSError as ose:
        logger.error("Error while running the command", ose)
        raise SystemExit

def start_agent(agent_name='snap.amazon-ssm-agent.amazon-ssm-agent.service'):
    try:
        os.popen(f"sudo systemctl start { agent_name }")
        logger.success("SSM Agent started successfully...")
    except OSError as ose:
        logger.error("Error while running the command", ose)
        raise SystemExit

def checkServiceStatus(service_unwanted_status='active', agent_name='snap.amazon-ssm-agent.amazon-ssm-agent.service'):
    try:
        #Check all the runnung service
        for line in os.popen(f"systemctl status { agent_name }"):
            if 'Active' in line:
                line = line.split()
                if line [1] == service_unwanted_status:
                    return True
                else:
                    return False          
    except OSError as ose:
        print("Error while running the command", ose)
        raise SystemExit
    return True

def get_public_ip():
    url = 'https://checkip.amazonaws.com'
    response = requests.get(url)
    if response.status_code == 200:
        public_ip = response.text.strip()
        logger.info(f'Current public IP is {public_ip}')
        return public_ip
    else:
        logger.error(f'Sorry, something went wrong. We couldn\'t retrieve the public IP')
        return None


def get_location_from_ip(ip):
    url = f'http://ipapi.co/{ip}/latlong/'
    response = requests.get(url)
    if response.status_code == 200:
        location = response.text.split(',')
        logger.info(f'GeoInfo: {float(location[0]), float(location[1])}')
        return float(location[0]), float(location[1])
    else:
        logger.error(f'Sorry, something went wrong. Couldn\'t get geolocation data')
        return None


def get_closest_aws_region(lat, lng):
    aws_regions = {
        'us-east-1': (37.7749, -122.4194),
        'us-east-2': (39.2904, -76.6122),
        'us-west-1': (37.3382, -121.8863),
        'us-west-2': (45.5231, -122.6765),
        'ca-central-1': (45.5017, -73.5673),
        'eu-central-1': (50.1109, 8.6821),
        'eu-west-1': (51.5074, -0.1278),
        'eu-west-2': (51.5074, -0.1278),
        'eu-west-3': (48.8566, 2.3522),
        'ap-northeast-1': (35.6895, 139.6917),
        'ap-northeast-2': (37.5665, 126.9780),
        'ap-southeast-1': (1.3521, 103.8198),
        'ap-southeast-2': (-33.8688, 151.2093),
        'ap-south-1': (19.0760, 72.8777),
        'sa-east-1': (-23.5505, -46.6333),
        'me-south-1': (25.2048, 55.2708),
        'af-south-1': (-33.9249, 18.4241),
    }

    closest_region = ''
    min_distance = float('inf')
    for region, (region_lat, region_lng) in aws_regions.items():
        distance = math.sqrt((lat - region_lat)**2 + (lng - region_lng)**2)
        if distance < min_distance:
            min_distance = distance
            closest_region = region
    # The following is for matching our current AWS regions. Should be removed later and work with the correct closest regions
    if closest_region == 'us-east-2':
        closest_region = 'us-east-1'
    if closest_region in ('us-west-2', 'ca-central-1'):
        closest_region = 'us-west-1'
    return closest_region