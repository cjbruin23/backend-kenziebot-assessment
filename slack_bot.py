import os
import time
import re
import sys
import signal
import logging
import datetime as dt
import pandas as pd
import pandas_datareader.data as web
from matplotlib import style
import matplotlib  
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from logging.handlers import RotatingFileHandler
from slackclient import SlackClient

# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
INSULT_COMMAND = "insult"
EXIT_COMMAND = "exit"
FINANCE_COMMAND = "get financials"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

watcher = False

def env_setup():

    # instantiate Slack client
    slack_client = SlackClient(os.getenv('SLACK_BOT_TOKEN', 'Token not found'))
    return slack_client


def signal_handler(sig_num, frame):
    if sig_num == 2:
        logging.warn('Shut down through command line')
        logger.warn('Shut down through command line')

        sys.exit(0)


def configure_logging():

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    global logger
    logger = logging.getLogger(__name__)

    logging.basicConfig(filename='slack_bot.log', 
                        level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    logging.basicConfig(filename='slack_bot.log',
                        level=logging.WARN,
                        format='%(asctime)s - %levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)


    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(sh)

    rh = logging.handlers.RotatingFileHandler('slack_bot.log', maxBytes=2000, backupCount=5)
    logger.addHandler(rh)


def parse_bot_commands(slack_events, starterbot_id):
    """
        Parses a list of events coming from the Slack RTM API to
        find bot commands.
        If a bot command is found, this function returns a tuple of
        command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
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


def handle_command(command, channel, slack_client, start_time):
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
        response = "Here are some commands to try: {0}, {1}, {2}".format(INSULT_COMMAND, FINANCE_COMMAND, INSULT_COMMAND)
    elif command.startswith(INSULT_COMMAND):
        command_lst = command.split(' ')
        insult_name = command_lst[1]
        response = "{} is ranked 14/14 in your cohort".format(insult_name)
    elif command.startswith(FINANCE_COMMAND):
            command_words = command.split(" ")
            start = dt.datetime(2000,1,1)
            end = dt.datetime.today()
            for word in command_words:
                if word.isupper():
                    try:
                        df = web.DataReader(word, 'yahoo', start, end)
                        stock_high = round(float(df["High"].iloc[-1]), 4)
                        stock_low = round(float(df["Low"].iloc[-1]), 4)
                        print(stock_high, stock_low)
                        response = "The High is {}, and the low is {}".format(stock_high, stock_low)
                    except:
                        response = "Sorry that is not a stock"
                else:
                    continue
            # response = "That is not a company. Make sure the companies ticker name is in uppercase"
    elif command.startswith(EXIT_COMMAND):
        global watcher
        watcher = True
        total_time = time.time() - start_time
        logging.info("Time up was {} seconds".format(total_time))
        response = "Time up was {} seconds".format(total_time)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


def main():
    
    slack_client = env_setup()
    configure_logging()
    try:
        if slack_client.rtm_connect(with_team_state=False):
            print("Starter Bot connected and running!")
            start_time = time.time()
            # logging.info('Bot started up')
            logger.info('Bot started up')

            # Read bot's user ID by calling Web API method `auth.test`
            starterbot_id = slack_client.api_call("auth.test")["user_id"]
            while not watcher:
                command, channel = parse_bot_commands(slack_client.rtm_read(), starterbot_id)
                if command:
                    # Formatting has a string conversion that helped avoid the TypeError
                    logging.info("Bot command given: {}".format(command.encode('utf-8')))
                    logger.info("Bot command given: {}".format(command.encode('utf-8')))
                    handle_command(command, channel, slack_client, start_time)
                time.sleep(RTM_READ_DELAY)
            if watcher:
                sys.exit(0)
        else:
            print("Connection failed. Exception traceback printed above.")
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()