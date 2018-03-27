class Config:
    debug = True
    gapi = '123'
    cseid = '123'

    discord_channel = '123'
    discord_token = '123'

    question_detection_y_range = range( 150, 950, 10 )
    question_detection_x_range = range( 1000, 1600, 10 )

    nextgame_bbox = (0,0,100,200)
    question_bbox = (0,0,100,200)
    answers_bbox = (0,0,100,200)

    reversewords = ['not']
