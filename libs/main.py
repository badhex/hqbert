import discord
import asyncio
from multiprocessing.pool import ThreadPool
import time
from datetime import datetime, timedelta

# PIL.ImageGrab is not supported on linux
import os
if os.name == 'nt':
	from PIL import ImageGrab
else:
	import pyscreenshot as ImageGrab

from config import Config
from libs import solver_google as solver
from libs import ocr

class G:
	client = discord.Client()
	pool = ThreadPool( processes=12 )

def get_color(x_range, y_range):
	total = (0, 0, 0)
	px = ImageGrab.grab().load()
	for y in y_range:
		for x in x_range:
			color = px[x, y]
			total = tuple( map( sum, zip( total, color ) ) )
	return total

async def main_task():
	await G.client.wait_until_ready()
	await asyncio.sleep( 3 )
	channel = discord.Object( id=Config.discord_channel )
	await G.client.change_presence( game=None )
	print( "Starting..." )
	waitforblack=False
	resultscreen=False
	gamestarted=False
	answer = ""
	ans = []
	num = 0

	while True:
		# determine when our next game is and wait
		gamedata = ocr.get_text('multiline', Config.nextgame_bbox, False, True)
		print("Game Data:", gamedata)
		if len(gamedata) == 4 and gamedata[0] == "NEXT GAME":
			t = datetime.today()
			try:
				nextgame = datetime.today().strptime( gamedata[2], '%I%p CDT' )
			except:
				nextgame = datetime.today().strptime( gamedata[2].replace("—", ""), '%m/%d %I%p CDT' )
			nextgame += timedelta()
			if t.hour >= nextgame.hour:
				nextgame += timedelta(days=1)
				print("Game starts in the past, pausing until tomorrow")
			if not Config.debug:
				await G.client.send_message( channel, "The next game starts " + gamedata[2] + " and has a " + gamedata[3] + "! See you then!" )
			print( "Sleeping for:", (nextgame-t).seconds, "seconds" )
			await asyncio.sleep( (nextgame-t).seconds )
		else:
			gamestarted = True

		if not gamestarted:
			if not Config.debug:
				await G.client.change_presence( game=None )
			continue
		else:
			if not Config.debug:
				await G.client.send_message( channel, "Hey guys, It's HQ time!!!!" )
				await G.client.change_presence( game=discord.Game( name='HQ Trivia' ) )

		gamestart = time.time()
		solution = None
		while True:
			print("While loop")
			if (time.time() - gamestart) > 1800:
				if not Config.debug:
					await G.client.change_presence( game=None )
				gamestarted = False
				print("Game has run for longer than 30 minutes, stopping loop.")
				break
			total = get_color(Config.question_detection_x_range, Config.question_detection_y_range)
			if Config.debug:
				print("color debug: ", total, " big total: ", sum(total))
			if sum(total) > 3100000:
				print("After sum check")
				
				if not waitforblack:
					print("After not waitforblack")
					if not resultscreen:
						print( "Found question!" )
						if Config.debug:
							await asyncio.sleep(1)
						async_question = G.pool.apply_async( ocr.get_text, ('question', Config.question_bbox, False) )
						async_answers = G.pool.apply_async( ocr.get_text, ('answers', Config.answers_bbox, False) )
						q = async_question.get()
						ans = async_answers.get()
						print( "question: ", q, " answers: ", ans )
						# if we only get two answers here, we were at the results screen and need to abort
						if len(ans) != 3 or not q or not q.endswith('?'):
							print("ERROR Reading question or answers! Trying again...")
							continue
						else:
							if not Config.debug:
								msg = "```ini\r\n[ " + q + " ]\r\n"
								i = 0
								for a in ans:
									msg += "#" + str(i+1) + " - " + a + "\r\n"
									i += 1
								msg += "```"
								await G.client.send_message( channel, msg )

							solution = solver.solve(q, ans)

							if not Config.debug:
								await G.client.send_message( channel, "I'm " + ("{:.1%}".format(solution['confidence'])) + " sure the answer is - #" + str(solution['num']+1) + " " + solution['answer'] )
								await G.client.send_message( channel, solution['msg'] )
							resultscreen = True
							waitforblack = True
							print("Exiting first case")
					elif solution and resultscreen and not waitforblack:
						print("In next case")
						await asyncio.sleep( 1 )
						px = ImageGrab.grab().load()
						correct = 0
						for i in range(3):
							green = [0,0,0]
							for y in range( 640+(i*115), 680+ (i*115), 1 ):
								for x in range( 1010, 1030, 1 ):
									color = px[x, y]
									green[i] += color[1] - ((color[0] + color[2]) / 2)
							if i == 0 or green[i-1] < green[i]:
								correct = i

						answer = solution['answer']
						print("The answer is #", correct+1, ans[correct], "I guessed #", ans.index(answer)+1, ans[ans.index(answer)])
						if not Config.debug:
							await G.client.send_message( channel, "Looks like I was %s, the correct answer was - #%s %s" % (("correct" if ans.index(answer) == correct else "WRONG"), str(correct+1), ans[correct]) )
						resultscreen = False
						waitforblack = True
						solution = None
			else:
				waitforblack = False

			await asyncio.sleep( 0.5 )


@G.client.event
async def on_ready():
	print( 'Logged in as' )
	print( G.client.user.name )
	print( G.client.user.id )
	print( '------' )


def start():
	G.client.loop.create_task( main_task() )
	G.client.run( Config.discord_token )
