from random import randint
from config import Config
from googleapiclient.discovery import build
from multiprocessing.pool import ThreadPool
import time

spool = ThreadPool( processes=5 )

rtypes = {
	1: "Google quick search",
	2: "Google result count",
	3: "Google full quick search"
}


def solve(question, answers):
	start_time = time.time()

	result = {}
	votes = []

	results = {
		1: spool.apply_async( calc_weight_google_glance, ( question, answers ) ),
		2: spool.apply_async( calc_weight_google_results, ( question, answers ) ),
		3: spool.apply_async( calc_weight_google_glance, ("%s %s" % (question, " ".join(answers)), answers) )
	}

	msg = "```"
	for k, v in results.items():
		result[k] = v.get()
		msg += ("\r\n" if k > 1 else "") + rtypes[k] + ":\r\n"
		correct = sorted( result[k], key=lambda tup: tup[3], reverse=(any( word in question for word in Config.reversewords )) )[-1]
		if correct[3] > 0.0 or any( word in question for word in Config.reversewords ):
			votes.append( correct[1] )
		for r in result[k]:
			msg += "# %s - %6s - %s %s\r\n" % (str( r[1] + 1 ), "{:.1%}".format( r[3] ), r[0], ("✓" if correct[1] == r[1] and (correct[3] > 0.0 or any( word in question for word in Config.reversewords )) else ""))
	msg += "```"

	if len(votes):
		c = max( votes, key=votes.count )
	else:
		print( "No votes, just guessing..." )
		c = randint(1, 3)

	# return most frequently voted for
	answer, num, raw, confidence = result[1][c]

	return {'answer': answer, 'num': num, 'confidence': confidence, 'msg': msg, 'votes': votes.count(num)}


def google_search(search_term, **kwargs):
	service = build( "customsearch", "v1", developerKey=Config.gapi )
	res = service.cse().list( q=search_term, cx=Config.cseid, **kwargs ).execute()
	return res


# determine the weight of answer by search results title and snippits
# takes:  question as string, answers as list of strings
# returns: list [(answer, number, raw, confidence), (answer, number, raw, confidence), (answer, number, raw, confidence)]
def calc_weight_google_glance(question, answers):
	question = question.replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" )
	results = google_search( question )
	result = [(), (), ()]
	total_i = 0
	if "items" in results:
		for item in results["items"]:
			a_num = 0
			for a in answers:
				junk, junk, a_i = result[a_num] if len( result[a_num] ) else (0, 0, 0)
				add1 = item['title'].lower().count( a.lower().replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" ) )
				add2 = item['snippet'].lower().count( a.lower().replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" ) )
				a_i += add1 + add2
				total_i += add1 + add2
				result[a_num] = (a, a_num, a_i)
				a_num += 1
	else:
		print("Search at a glance error: Items not in results")
		a_num = 0
		for a in answers:
			result[a_num] = (a, a_num, 0)
			a_num += 1

	# now that we have all the answers, figure out the percentages
	a_num = 0
	for r in result:
		a, n, a_i = r
		percent = (float( a_i ) / float( total_i )) if total_i > 0 else 0.0
		result[a_num] = (a, n, a_i, percent)
		a_num += 1

	return result


# determine the weight of answer by number of search results
# takes:  question as string, answers as list of strings
# returns: list [(answer, number, raw, confidence), (answer, number, raw, confidence), (answer, number, raw, confidence)]
def calc_weight_google_results(question, answers):
	question = question.replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" )
	result = [(), (), ()]
	total_i = 0
	a_num = 0
	for a in answers:
		results = google_search( question.replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" ),
		                         exactTerms=a.replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" ) )
		result[a_num] = (a, a_num, int( results['searchInformation']['totalResults'] ))
		total_i += int( results['searchInformation']['totalResults'] )
		a_num += 1
	# now that we have all the answers, figure out the percentages
	a_num = 0
	for r in result:
		a, n, a_i = r
		percent = (float( a_i ) / float( total_i )) if total_i > 0 else 0.0
		result[a_num] = (a, n, a_i, percent)
		a_num += 1

	return result
