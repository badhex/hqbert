from libs.ocr import Screen
from config import Config

if __name__ == '__main__':
	sc = Screen( Config.answers_bbox )
	sc.write()
	print( sc.selected() )
