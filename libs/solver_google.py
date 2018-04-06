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
	results = {
		1: spool.apply_async( calc_weight_google_glance, ( question, answers ) ),
		2: spool.apply_async( calc_weight_google_results, ( question, answers ) ),
		3: spool.apply_async( calc_weight_google_glance, ("%s %s" % (question, " ".join(answers)), answers) )
	}

	votes = []
	msg = "```"
	for k, r in results.items():
		result[k] = r.get()

		# get the index of the highest percent
		correct = sorted( result[k], key=lambda tup: tup[3], reverse=(any( word in question for word in Config.reversewords )) )[-1]
		votes.append(correct[1])

		msg += ("\r\n" if k > 1 else "") + rtypes[k] + ":"
		for re in result[k]:
			msg += "# %s - %6s - %s %s\r\n" % (str( re[1] + 1 ), "{:.1%}".format( re[3] ), re[0], ("✓" if correct[1] == re[1] else ""))
	msg += "```"

	if Config.debug:
		print("Result: ", result[max( votes, key=votes.count )])
	# return most frequently voted for
	answer, num, raw, confidence = result[max( votes, key=votes.count )]

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
