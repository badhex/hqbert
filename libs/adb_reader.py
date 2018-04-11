from bs4 import BeautifulSoup
import datetime
from libs.subprocess import run_asyncio_commands, run_command_shell
from config import Config

screens = {
	"NEXT_GAME": "com.intermedia.hq:id/next_game_container",
	"QA": "com.intermedia.hq:id/question_view_layout",
	"RESULT": "com.intermedia.hq:id/answer_result_view_container",
	"ELIMINATED": ""
}

class HQscreen:
	def __init__(self):
		self.__xml__ = run_asyncio_commands( [run_command_shell( Config.ADB.path + " exec-out uiautomator dump --force-view-server-use --all /dev/tty" ), ], 1 )[0]
		self.soup = BeautifulSoup( self.__xml__, "lxml" )
		self.displayed = None
		self.next_game = None
		self.qa = None
		self.result = None

		# Searching xml by priority
		# First QA Screen
		self.qa_node = self.soup.find( "node", attrs={"resource-id": screens['QA']} )
		if self.qa_node:
			self.displayed = "QA"
			self.qa = {
				"question": self.qa_node.find("node", attrs={"resource-id": "com.intermedia.hq:id/question"})['text'],
				"a1": self.qa_node.find( "node", attrs={"resource-id": "com.intermedia.hq:id/answer_button_one"} )['text'],
				"a2": self.qa_node.find( "node", attrs={"resource-id": "com.intermedia.hq:id/answer_button_two"} )['text'],
				"a3": self.qa_node.find( "node", attrs={"resource-id": "com.intermedia.hq:id/answer_button_three"} )['text'],
			}
		else:
			# Second RESULT
			self.result_node = self.soup.find( "node", attrs={"resource-id": screens['RESULT']} )
			if self.result_node:
				self.result = {
					"a1": self.result_node.find( "node", attrs={"resource-id": "com.intermedia.hq:id/answer_result_one"} )['text'],
					"a1": self.result_node.find( "node", attrs={"resource-id": "com.intermedia.hq:id/answer_result_two"} )['text'],
					"a1": self.result_node.find( "node", attrs={"resource-id": "com.intermedia.hq:id/answer_result_three"} )['text'],
				}
				# somehow detect which question is green
			else:
				# Third the Eliminated window

				# Lastly NEXT_GAME screen
				self.next_game_node = self.soup.find( "node", attrs={"resource-id": screens['NEXT_GAME']} )
				if self.next_game_node:
					self.displayed = "NEXT_GAME`"
					self.next_game = {
						"time":  self.next_game_node.find( "node", attrs={"resource-id": "com.intermedia.hq:id/next_time_label"} )['text'],
						"prize": self.next_game_node.find( "node", attrs={"resource-id": "com.intermedia.hq:id/prize_amount_label"} )['text']
					}

	def save_xml(self):
		uniq_filename = str( datetime.datetime.now().date() ) + '_' + str( datetime.datetime.now().time() ).replace( ':', '.' ) + ".xml"
		with open( uniq_filename, 'w' ) as f:
			f.write( self.__xml__ )

		print("XML Saved as:", uniq_filename)
