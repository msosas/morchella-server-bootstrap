from config import Config
from slacker import Slacker
from loguru import logger

class MessageNotFound(Exception):
    pass
class ChannelNotFound(Exception):
    pass

def handler(event, context=None):

    logger.debug(f'{event} is a {type(event)}')
    
    if isinstance(event, dict):
        if 'Records' in event.keys(): # For AWS SQS 
            config = Config(slack_channel=event['Records'][0]['messageAttributes']['channel']['stringValue'])
            slacker = Slacker(config)
            slacker.send_message(message=event['Records'][0]['body'], parser='sqs_parser')
            return

        if 'channel' in event.keys():
            config = Config(slack_channel=event['channel'])
            slacker = Slacker(config)
            slacker.send_message(message=event)
        else:
            raise ChannelNotFound('Channel not found ')
        # else:
        #     raise MessageNotFound('Message not found ')
    else:
        if isinstance(event, str):
            config = Config()
            slacker = Slacker(config)
            slacker.send_message(message=event)

    

if __name__ == '__main__':   
    event = "{'message': 'value1', 'channel': '#general', 'log_level': 'info', 'username': 'Slackbot'}"
    handler(event)