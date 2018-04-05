from TwitterSearch import *

try:
    tuo = TwitterUserOrder('NeinQuarterly') # create a TwitterUserOrder

    # it's about time to create TwitterSearch object again
    ts = TwitterSearch(
        consumer_key = 'aaabbb',
        consumer_secret = 'cccddd',
        access_token = '111222',
        access_token_secret = '333444'
    )

    # start asking Twitter about the timeline
    for tweet in ts.search_tweets_iterable(tuo):
        print( '@%s tweeted: %s' % ( tweet['user']['screen_name'], tweet['text'] ) )

except TwitterSearchException as e: # catch all those ugly errors
    print(e)