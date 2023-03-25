from loguru import logger
from datetime import datetime
from config import Config
import pytz

from requests import post as requests_post

class Slacker:
    """
    A Slack notifications class
    """
    def __init__(self, config: Config): 
        self.config = config
        self.slack_channel = config.get_slack_channel()
        self.slack_username = config.get_slack_username()
        self.log_level = 20
        self.msg = None

    log_level_to_icons = {
        logger.level('CRITICAL').no: ":skull:",
        logger.level('ERROR').no: ":x:",
        logger.level('WARNING').no: ":warning:",
        logger.level('INFO').no: ":information_source:",
        logger.level('DEBUG').no: ":beetle:",
    }

    log_level_to_colors = {        
        logger.level('CRITICAL').no: "#FF3333",
        logger.level('ERROR').no: "#99004C",
        logger.level('WARNING').no: "#FF8000",
        logger.level('INFO').no: "#0080FF",
        logger.level('DEBUG').no: "#9733EE",
    }


    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    def log_level_to_int(self, log_level):
        return (self.log_levels.index(log_level) + 1)*10

    def validate_message(self, message):
        if not message:
            logger.warning('Empty message. Request not sent')
            return False
        else:
            if not 'channel' in message.keys():
                message['channel'] = self.slack_channel

        return True



    ## Begin of Parsers:

    def default_parser(self, message):
        if isinstance(message, str):
            import json
            try:
                message = json.loads(message)
            except Exception as e:
                logger.warning(f'{message} cannot be converted to an json object. Reason:\n{e}')
                self.set_msg(message)

        if isinstance(message, dict):                
            if 'username' in message.keys():
                self.set_slack_username(message['username'])                
            if 'message' in message.keys():
                self.set_msg(message['message'])
            if 'log_level' in message.keys():
                self.set_log_level(message['log_level'])

        # https://api.slack.com/messaging/composing/layouts
        
        date = datetime.now(pytz.timezone('Pacific/Auckland'))
        date_string = date.strftime("%Y-%m-%d %H:%M:%S")


        parsed_msg = {
            "icon_emoji": ":construction:",
            "username": self.get_slack_username(),
            "channel": self.get_slack_channel(),
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{self.log_level_to_icons[self.log_level]} *{self.log_levels[self.log_level//10 - 1 ]}*"
                    }
                },                
            ],
            "attachments": [
                {
                    "color": f"{self.log_level_to_colors[self.log_level]}",
                    "fallback": "Ups, looks like something is not well",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "`" + date_string + "` - " + self.msg + ""
                            }
                        },
                        {
                            "type": "divider"
                        },
                    ], 

                }
            ]
        }
        return parsed_msg

       
    def sqs_parser(self, event: str):
        import json
        """
        BODY:
        { "message": "test", "log_level": "CRITICAL"}
        """
     
        logger.debug(event)
        body = json.loads(f'{event}')
        if 'message' in body:
            message = body['message']

        if 'log_level' in body.keys():           
            self.set_log_level(body['log_level'])

        return self.default_parser(message)
        
        
    
    def parse_icinga2_msg(self, message, log_level=20):
        pass
    def parse_ubuntu_watchdog_msg(self, message, log_level=20):
        pass

    # def morchella_parser(self, message, log_level=20):
    #     parsed_msg = self.default_parser(message)
    #     parsed_msg['attachments']['blocks'],append(

    #     )
    #     return 
    
    
    ## End of parsers 


    def send_message(self, message, log_level=None, parser=None):
        if log_level is not None:
            
            self.set_log_level(log_level)       
        if parser is None:
            logger.debug('Using default parser')
            message =self.default_parser(message)
        else:
            if '__' in parser:
                raise NameError('Parser name not allowed')
            parser = getattr(self, parser)
            logger.debug(f'Using {parser}')
            message = parser(message)
        
        if self.validate_message(message):
            result = requests_post(
                url=self.config.get_slack_hook(),
                json = message,
                headers={"Content-Type": "application/json"},
            )
        else:
            logger.error('Invalid message')
        logger.debug(result)

    def get_slack_username(self) -> str:
        return self.slack_username

    def set_slack_username(self, username) -> None:
        self.slack_username = username

    def get_slack_channel(self) -> str:
        return self.slack_channel

    def set_log_level(self, log_level):
        if isinstance(log_level, str ):
            log_level = log_level.upper()
            log_level = self.log_level_to_int(log_level)
        self.log_level = log_level
    def set_msg(self, msg: str = None) -> None:
        self.msg = msg