# Morchella - Server Bootstrap

This is a simple Python script that allows you to connect a server to AWS System Manager (SSM) using the AWS SSM agent. This can be useful for managing on-prem /edge instances using AWS.

The script has been tested on Ubuntu server: 18.04, 20.04 and 22.04

## Prerequisites

Before running this script, you will need to make sure that you have the following:

- An AWS account with appropriate permissions to access the AWS SSM service
- SSM Agent. [Official Docs](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-manual-agent-install.html)
- Python 3.9 installed on the server
- Pip3 and virtualenv
- Slack hook

## Installation

1. To install this script, simply download or clone this repository onto the Linux server.
2. Create a new virtual environment
  ```
  cd <project_name>
  python3 -m virtualenv .venv
  source .venv/bin/activate
  ```
3. Install the required libraries
  ```
  pip install -r requirements.txt
  ```
4. Use the project [morchella-aws-infra](https://github.com/msosas/morchella-aws-infra) to deploy the needed infrastructure on AWS

5. Create a config.ini file
```
# config.ini

[CREDENTIALS]
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION = "" # this is optional since the server finds the closest region if it's not defined here

[SLACK]
SLACK_WEB_HOOK = ""
SLACK_CHANNEL = #general

[MORCHELLA]
AUTO_REGISTER = -y

```


## Contributing

If you find any issues with this script or would like to suggest improvements, please feel free to open an issue or submit a pull request on GitHub.

## License

This script is licensed under the MIT License.