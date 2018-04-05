
class Config:
	debug = True
	debug_question_bbox = False
	debug_answers_bbox = False
	debug_nextgame_bbox = False
	upscale_ocr = 600

	gapi = '123'
	cseid = '123'

	discord_channel = '123'
	discord_token = '123'

	screen_detection_bbox = (950, 150, 1600, 1000)
	question_threshhold = 3100000

	nextgame_bbox = (0,0,100,200)
	question_bbox = (0,0,100,200)
	answers_bbox = (0,0,100,200)

	reversewords = ['not']

	class DB:
		enabled = False
		host = 'localhost'
		user = 'hqbert'
		password = 'pass'
		db = 'hqbert'
		table = 'qa'
		charset = 'utf8mb4'
