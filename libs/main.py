import discord
import asyncio
import time
from datetime import datetime, timedelta

from config import Config
from libs import solver_google as solver
from libs.ocr import Screen


class G:
	client = discord.Client()


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
	ans = []

	while True:
		###########################################################
		# Pre-Game Check and pause
		###########################################################
		sc = Screen(Config.nextgame_bbox, show=Config.debug_nextgame_bbox)
		color = sc.average_color()
		if color[0] < color[2] and color[1] < color[2]:
			gamedata = sc.text(True)
			print("Game Data:", gamedata)
			if len(gamedata) == 3 and gamedata[0] == "NEXT GAME":
				t = datetime.today()
				try:
					nextgame = datetime.today().strptime( gamedata[1], '%I%p CDT' )
				except:
					nextgame = datetime.today().strptime( gamedata[1].replace("—", ""), '%m/%d %I%p CDT' )
				nextgame += timedelta()
				if t.hour >= nextgame.hour:
					print("Game starts in the past, waiting for it to start...")
					await asyncio.sleep( 10 )
				else:
					if not Config.debug:
						await G.client.send_message( channel, "The next game starts " + gamedata[1] + " and has a " + gamedata[2] + "! See you then!" )
					print( "Sleeping for:", (nextgame-t).seconds, "seconds" )
					await asyncio.sleep( (nextgame-t).seconds )
			else:
				gamestarted = True
		else:
			gamestarted = True

		if not gamestarted:
			continue

		###########################################################
		# Game starting
		###########################################################
		if not Config.debug:
			await G.client.send_message( channel, "Hey guys, It's HQ time!!!!" )
			await G.client.change_presence( game=discord.Game( name='HQ Trivia' ) )

		gamestart = time.time()
		solution = None
		while True:
			print("Main loop")
			if (time.time() - gamestart) > 1800:
				if not Config.debug:
					await G.client.change_presence( game=None )
				gamestarted = False
				print("Game has run for longer than 30 minutes, stopping loop.")
				break

			total = sum(Screen(Config.screen_detection_bbox).color_sum(10))
			if Config.debug:
				print("color debug: ", total)

			if total > 3100000:
				print("After sum check")
				
				if not waitforblack:
					print("After not waitforblack")
					if not resultscreen:
						print( "Found question!" )
						if Config.debug:
							await asyncio.sleep(1)
						q, ans = (Screen(Config.question_bbox, show=Config.debug_question_bbox).text(), Screen(Config.answers_bbox, show=Config.debug_answers_bbox).text(True))
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
						correct = Screen(Config.answers_bbox).selected()
						if correct == -1:
							print("Could not determine answer... bail bail")
							continue

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
