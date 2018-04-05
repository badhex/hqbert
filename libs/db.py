import base64
import pymysql.cursors

from config import Config


def writeq(q, ans, correct, answered, qimage=None, aimage=None):
	if Config.DB.enabled:
		connection = pymysql.connect( host=Config.DB.host, user=Config.DB.user, password=Config.DB.password, db=Config.DB.db, charset=Config.DB.charset,
		                              cursorclass=pymysql.cursors.DictCursor )
		try:
			with connection.cursor() as cursor:
				sql = "INSERT INTO `" + Config.DB.table + "` (`q`, `a1`, `a2`, `a3`, `correct`, `answered`, `qimage`, `aimage`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
				cursor.execute( sql, (q, ans[0], ans[1], ans[2], int( correct ), int( answered ), base64.b64encode( qimage.tobytes() ), base64.b64encode( aimage.tobytes() )) )
			connection.commit()
		finally:
			connection.close()
