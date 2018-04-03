import pymysql.cursors

from config import Config

connection = pymysql.connect( host=Config.DBcfg.host, user=Config.DBcfg.user, password=Config.DBcfg.password, db=Config.DBcfg.db, charset=Config.DBcfg.charset, cursorclass=pymysql.cursors.DictCursor )


def writeq(q, ans, correct, answered):
	try:
		with connection.cursor() as cursor:
			# Create a new record
			sql = "INSERT INTO `" + Config.DBcfg.table + "` (`q`, `a1`, `a2`, `a3`, `correct`, `answered`) VALUES (%s, %s, %s, %s, %s, %s)"
			cursor.execute( sql, (q, ans[0], ans[1], ans[2], int(correct), int(answered)) )

		# connection is not autocommit by default. So you must commit to save your changes.
		connection.commit()
	finally:
		connection.close()
