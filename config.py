import logging
from os import getenv

logger = logging.getLogger(__name__)

class WebHookMissingException(Exception):
    def __init__(self):
        super().__init__(f'Slack web hook is is missing. Try setting SLACK_WEB_HOOK env var')        


class Config:  # pylint: disable=R0904,W0511
    def __init__(self, slack_web_hook: str='', slack_username: str='Morchella Notification', slack_channel: str='general'):
        if slack_web_hook == '':
            if getenv('SLACK_WEB_HOOK') != None:
                self.slack_web_hook = getenv('SLACK_WEB_HOOK')
            else:
                raise WebHookMissingException()
        else:
            self.slack_web_hook = slack_web_hook
        self.slack_username = slack_username
        self.slack_channel = slack_channel

    def get_slack_hook(self) -> str:
        return self.slack_web_hook
    
    def get_slack_username(self) -> str:
        return self.slack_username

    def set_slack_username(self, username) -> None:
        self.slack_username = username
    
    def get_slack_channel(self) -> str:
        return self.slack_channel

