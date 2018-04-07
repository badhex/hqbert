from bs4 import BeautifulSoup
import datetime
from libs.subprocess import run_asyncio_commands, run_command_shell
from config import Config

screens = {
	"NEXT_GAME": "com.intermedia.hq:id/next_game_container"
}

class HQscreen:
	def __init__(self):
		self.__xml__ = run_asyncio_commands( [run_command_shell( Config.ADB.path + " exec-out uiautomator dump /dev/tty" ), ], 1 )[0]
		self.soup = BeautifulSoup( self.__xml__, "lxml" )
		self.displayed = None
		self.next_game = None

		self.next_game_node = self.soup.find("node", attrs={"resource-id": screens['NEXT_GAME']})
		if self.next_game_node:
			self.displayed = "NEXT_GAME`"
			self.next_game = {
				"time": self.next_game_node.find("node", attrs={"resource-id": "com.intermedia.hq:id/next_time_label"})['text'],
				"prize": self.next_game_node.find("node", attrs={"resource-id": "com.intermedia.hq:id/prize_amount_label"})['text']
			}

	def save_xml(self):
		uniq_filename = str( datetime.datetime.now().date() ) + '_' + str( datetime.datetime.now().time() ).replace( ':', '.' ) + ".xml"
		with open( uniq_filename, 'w' ) as f:
			f.write( self.__xml__ )

		print("XML Saved as:", uniq_filename)
