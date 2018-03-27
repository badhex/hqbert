import pytesseract
from PIL import ImageEnhance, ImageOps

# PIL.ImageGrab is not supported on linux
import os
if os.name == 'nt':
	from PIL import ImageGrab
else:
	import pyscreenshot as ImageGrab

from config import Config

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

