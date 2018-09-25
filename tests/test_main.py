import unittest
import subprocess
import sys
import slack_bot

class TestStringMethods(unittest.TestCase):

    def test_bot_commands(self):
        slack_bot.starterbot_id = "UCQ6VHPKN"
        self.assertEqual(slack_bot.parse_bot_commands(
            [{'client_msg_id': '2185d748-b54f-48ad-8609-83692726e801',
            'event_ts': '1536680134.000100', 'text': '<@UCQ6VHPKN> exit', 
            'ts': '1536680134.000100', 'user': 'UCNFFQTDY', 'team': 'TCDBX31NH', 
            'type': 'message', 'channel': 'DCPRDV43T'}]), ('exit', 'DCPRDV43T'))


if __name__ == '__main__':
    unittest.main()