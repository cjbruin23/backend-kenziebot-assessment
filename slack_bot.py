import os
import time
import re
import sys
from slackclient import SlackClient
from dotenv import load_dotenv

# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
INSULT_COMMAND = "insult"
EXIT_COMMAND = "exit"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

watcher = False


def env_setup():
    dotenv_path = os.path.join(os.path.dirname('main.py'), '.env')
    load_dotenv(dotenv_path)

    # instantiate Slack client
    slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
    return slack_client


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to
        find bot commands.
        If a bot command is found, this function returns a tuple of
        command and channel.
        If its not found, then this function returns None, None.
    """
    print 'test input', slack_events
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            print 'event text:', event["text"]
            user_id, message = parse_direct_mention(event["text"])
            print user_id, starterbot_id
            if user_id == starterbot_id:
                print 'test output', message, event["channel"]
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning)
        in message text and returns the user ID which was mentioned.
        If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username,
    # the second group contains the remaining message
    return (matches.group(1),
            matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_string = "Not sure what you mean. Try *{}*."
    default_response = default_string.format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    elif command.startswith(INSULT_COMMAND):
        command_lst = command.split(' ')
        insult_name = command_lst[1]
        response = "{} is ranked 14/14 in your cohort".format(insult_name)
    elif command.startswith(EXIT_COMMAND):
        global watcher
        watcher = True
        response = "Bye Bye"
        

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


if __name__ == "__main__":
    slack_client = env_setup()
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while not watcher:
            print watcher
            print 'running'
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
        if watcher:
            sys.exit(0)
    else:
        print("Connection failed. Exception traceback printed above.")