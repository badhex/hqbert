from config import Config
from googleapiclient.discovery import build
from multiprocessing.pool import ThreadPool
import time

spool = ThreadPool( processes=5 )


def solve(question, answers):
	start_time = time.time()
	async_result = spool.apply_async( calc_weight_google_glance, ( question, answers ) )
	async_result2 = spool.apply_async( calc_weight_google_results, (question, answers) )
	async_result3 = spool.apply_async( calc_weight_google_glance_grouped, (question, answers) )

	# search google for the question and count the occurances of the answer
	result = async_result.get()
	sorted_by_second = sorted( result, key=lambda tup: tup[3], reverse=(any( word in question for word in Config.reversewords )) )
	answer, num, raw, confidence = sorted_by_second.pop()
	print( "--- %s seconds ---" % (round( time.time() - start_time, 2 )), "calc_weight_google_glance:", "{:.1%}".format( confidence ), num, answer, "raw:", result )
	result2 = async_result2.get()
	if raw < 10 and confidence < 0.34:
		sorted_by_second = sorted( result2, key=lambda tup: tup[3], reverse=(any( word in question for word in Config.reversewords )) )
		answer, num, raw, confidence = sorted_by_second.pop()
		print( "--- %s seconds ---" % (round( time.time() - start_time, 2 )), "calc_weight_google_results:", "{:.1%}".format( confidence ), num, answer, "raw:", result )

	# new search type searches whole question and all answers together
	result3 = async_result3.get()

	msg = "```Google quick search:\r\n"
	for r in result:
		msg += "# %s - %6s - %s\r\n" % (str( r[1] + 1 ), "{:.1%}".format( r[3] ), r[0])
	msg += "\r\nGoogle result count:\r\n"
	for r in result2:
		msg += "# %s - %6s - %s\r\n" % (str( r[1] + 1 ), "{:.1%}".format( r[3] ), r[0])
	msg += "\r\nGoogle full quick search:\r\n"
	for r in result3:
		msg += "# %s - %6s - %s\r\n" % (str( r[1] + 1 ), "{:.1%}".format( r[3] ), r[0])
	msg += "```"

	return {'answer': answer, 'num': num, 'confidence': confidence, 'msg': msg}


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

# determine the weight of answer by search results title and snippits including answers in full search
# takes:  question as string, answers as list of strings
# returns: list [(answer, number, raw, confidence), (answer, number, raw, confidence), (answer, number, raw, confidence)]
def calc_weight_google_glance_grouped(question, answers):
	question = question.replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" )
	result = [(), (), ()]
	total_i = 0
	a_num = 0
	results = google_search( "%s %s" % (question.replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" ), " ".join(answers).replace( '"', "" ).replace( ',', "" ).replace( "‘", "" ).replace( ".", "" )) )
	for a in answers:
		for i in results['items']:
			result[a_num] += i["title"].count(a) + i["snippet"].count(a)
		total_i += result[a_num]
		a_num += 1
	# now that we have all the answers, figure out the percentages
	a_num = 0
	for r in result:
		a, n, a_i = r
		percent = (float( a_i ) / float( total_i )) if total_i > 0 else 0.0
		result[a_num] = (a, n, a_i, percent)
		a_num += 1

	return result