import discord
import asyncio
from multiprocessing.pool import ThreadPool
from googleapiclient.discovery import build
import time
import pytesseract
from PIL import ImageGrab, ImageEnhance, ImageOps
from datetime import datetime, timedelta

from config import Config


class G:
	client = discord.Client()
	pool = ThreadPool( processes=12 )

def google_search(search_term, **kwargs):
	service = build( "customsearch", "v1", developerKey=Config.gapi )
	res = service.cse().list( q=search_term, cx=Config.cseid, **kwargs ).execute()
	return res


# determine the weight of answer by search results title and snippits
# takes:  question as string, answers as list of strings
# returns: list [(answer, number, raw, confidence), (answer, number, raw, confidence), (answer, number, raw, confidence)]
def calc_weight_google_glance(question, answers):
	question = question.replace('"', "").replace(',', "").replace("‘", "").replace(".", "")
	results = google_search( question )
	result = [(),(),()]
	total_i = 0
	for item in results["items"]:
		a_num = 0
		for a in answers:
			junk, junk, a_i = result[a_num] if len(result[a_num]) else (0,0,0)
			add1 = item['title'].lower().count(a.lower().replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" ))
			add2 = item['snippet'].lower().count(a.lower().replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" ))
			a_i += add1 + add2
			total_i += add1 + add2
			result[a_num] = (a, a_num, a_i)
			a_num += 1
	# now that we have all the answers, figure out the percentages
	a_num = 0
	for r in result:
		a, n, a_i = r
		percent = (float(a_i) / float(total_i)) if total_i > 0 else 0.0
		result[a_num] = (a, n, a_i, percent)
		a_num += 1

	return result

# determine the weight of answer by number of search results
# takes:  question as string, answers as list of strings
# returns: list [(answer, number, raw, confidence), (answer, number, raw, confidence), (answer, number, raw, confidence)]
def calc_weight_google_results(question, answers):
	question = question.replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" )
	result = [(),(),()]
	total_i = 0
	a_num = 0
	for a in answers:
		results = google_search( question.replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" ), exactTerms=a.replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" ) )
		result[a_num] = (a, a_num, int( results['searchInformation']['totalResults'] ))
		total_i += int( results['searchInformation']['totalResults'] )
		a_num += 1
	# now that we have all the answers, figure out the percentages
	a_num = 0
	for r in result:
		a, n, a_i = r
		percent = (float(a_i) / float(total_i)) if total_i > 0 else 0.0
		result[a_num] = (a, n, a_i, percent)
		a_num += 1

	return result


def get_text(kind, box, showcap=False, invert_img=False):
	im = ImageGrab.grab( bbox=box )

	if Config.debug or True:
		contrast = ImageEnhance.Contrast( im )
		im = contrast.enhance(2)

	if invert_img:
		im = im.convert('L')
		im = ImageOps.invert(im)

	if showcap:
		im.show()

	if kind is 'question':
		return (" ".join( pytesseract.image_to_string( im ).split() )).replace( "— ", "" )
	elif kind is 'answers':
		answers = pytesseract.image_to_string( im, lang='eng', config='-psm 3' ).splitlines()
		if not answers:
			# fix for single character questions
			print("Processing solo character...")
			imgwidth, imgheight = im.size
			count = 0
			for i in range( 0, int(imgheight), int(imgheight/3) ):
				if count >= 3:
					break
				box = (0, i, imgwidth/2, i + int(imgheight/3))
				a = im.crop( box )
				ans = pytesseract.image_to_string( a, lang='eng', config='-psm 10' ).splitlines()
				if ans:
					answers.append(ans[0])
					count += 1
		return list( filter( None, answers ) )
	elif kind is 'multiline':
		return pytesseract.image_to_string( im, lang='eng', config='-psm 3' ).splitlines()
	else:
		# just return the data that is in our box
		return " ".join( pytesseract.image_to_string( im ).split() )


async def my_background_task():
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
		gamedata = get_text('multiline', Config.nextgame_bbox, False, True)
		print("Game Data:", gamedata)
		if len(gamedata) == 4 and gamedata[0] == "NEXT GAME":
			t = datetime.today()
			nextgame = datetime.today().strptime( gamedata[2], '%I%p CDT' )
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
		while True:
			if (time.time() - gamestart) > 1800:
				if not Config.debug:
					await G.client.change_presence( game=None )
				gamestarted = False
				print("Game has run for longer than 30 minutes, stopping loop.")
				break
			total = (0, 0, 0)
			px = ImageGrab.grab().load()
			for y in range( 150, 950, 10 ):
				for x in range( 1000, 1600, 10 ):
					color = px[x, y]
					total = tuple( map( sum, zip( total, color ) ) )
			if Config.debug:
				print("color debug: ", total, " big total: ", sum(total))
			if sum(total) > 3100000:
				if not waitforblack:
					if not resultscreen:
						start_time = time.time()
						print( "Found question!" )
						if Config.debug:
							await asyncio.sleep(1)
						async_question = G.pool.apply_async( get_text, ('question', Config.question_bbox, False) )
						async_answers = G.pool.apply_async( get_text, ('answers', Config.answers_bbox, False) )
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

							# if we match at a glance, we're probably correct
							fullsearch = False
							# search google for the question and count the occurances of the answer
							result = calc_weight_google_glance( q, ans )
							sorted_by_second = sorted( result, key=lambda tup: tup[3], reverse=(any( word in q for word in Config.reversewords )) )
							answer, num, raw, confidence = sorted_by_second.pop()
							print("Matched at a glance!")
							print( "--- %s seconds ---" % (round( time.time() - start_time, 2 )), "calc_weight_google_glance:", "{:.1%}".format(confidence), num, answer, "raw:", result )
							if raw < 10 and confidence < 0.34:
								fullsearch = True
								# search google for the question including the answer and see if the answers are in the results
								result2 = calc_weight_google_results(q, ans)
								sorted_by_second = sorted( result2, key=lambda tup: tup[3], reverse=(any(word in q for word in Config.reversewords))  )
								answer, num, raw, confidence = sorted_by_second.pop()
								print( "Matched after full search!" )
								print( "--- %s seconds ---" % (round(time.time() - start_time, 2)), "calc_weight_google_results:", "{:.1%}".format(confidence), num, answer, "raw:", result )

							if not Config.debug:
								await G.client.send_message( channel, "I'm " + ("{:.1%}".format(confidence)) + " sure the answer is - #" + str(num+1) + " " + answer )

								msg = "```Google quick search:\r\n"
								for r in result:
									msg += "# %s - %6s - %s\r\n" % (str(r[1]+1), "{:.1%}".format(r[3]), r[0] )
								if fullsearch:
									msg += "\r\nGoogle result count:\r\n"
									for r in result2:
										msg += "# %s - %6s - %s\r\n" % (str( r[1] + 1 ), "{:.1%}".format( r[3] ), r[0])
								msg += "```"
								await G.client.send_message( channel, msg )
							resultscreen = True
							waitforblack = True
					elif answer and num and resultscreen and not waitforblack:
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

						print("The answer is #", correct+1, ans[correct], "I guessed #", ans.index(answer)+1, ans[ans.index(answer)])
						if not Config.debug:
							await G.client.send_message( channel, "Looks like I was %s, the correct answer was - #%s %s" % (("correct" if ans.index(answer) == correct else "WRONG"), str(correct+1), ans[correct]) )
						resultscreen = False
						waitforblack = True
			else:
				waitforblack = False

			await asyncio.sleep( 0.5 )


@G.client.event
async def on_ready():
	print( 'Logged in as' )
	print( G.client.user.name )
	print( G.client.user.id )
	print( '------' )


if __name__ == '__main__':
	G.client.loop.create_task( my_background_task() )
	G.client.run( Config.discord_token )
