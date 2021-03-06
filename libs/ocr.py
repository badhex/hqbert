import pytesseract
from PIL import ImageEnhance, ImageOps
from math import floor

# PIL.ImageGrab is not supported on linux
import os

if os.name == 'nt':
	from PIL import ImageGrab
else:
	import pyscreenshot as ImageGrab

from multiprocessing.pool import ThreadPool
from config import Config

pool = ThreadPool( processes=5 )


class Screen:
	def __init__(self, bbox=(0, 0, 0, 0), **kwargs):
		self.bbox = bbox
		if self.bbox:
			self.im = ImageGrab.grab( self.bbox )
		else:
			self.im = ImageGrab.grab()

		if "upscale" in kwargs.items() and kwargs["upscale"] is True:
			w, h = self.im.size
			ratio = Config.upscale_ocr / w
			self.im = self.im.resize( (int( w * ratio ), int( h * ratio )) )

		if "enhance" in kwargs.items() and kwargs["enhance"] is True:
			contrast = ImageEnhance.Contrast( self.im )
			self.im = contrast.enhance( 2 )

		if "invert" in kwargs.items() and kwargs["invert"] is True:
			self.im = ImageOps.invert( self.im )

		if "grayscale" in kwargs.items() and kwargs["grayscale"] is True:
			self.im = self.im.convert( 'L' )

		if "show" in kwargs.items() and kwargs["show"] is True:
			self.im.show()

	# accepts area to looks for text
	# returns boolean
	def is_text(self, text, multiline=False):
		return False

	# returns average weight of colors
	def average_color(self):
		h = self.im.histogram()

		# split into red, green, blue
		r = h[0:256]
		g = h[256:256 * 2]
		b = h[256 * 2: 256 * 3]

		# perform the weighted average of each channel:
		# the *index* is the channel value, and the *value* is its weight
		return (
			(sum( i * w for i, w in enumerate( r ) ) / sum( r )) if sum( r ) > 0 else 0,
			(sum( i * w for i, w in enumerate( g ) ) / sum( g )) if sum( g ) > 0 else 0,
			(sum( i * w for i, w in enumerate( b ) ) / sum( b )) if sum( b ) > 0 else 0
		)

	# accepts int as step for how man pixels to step
	# returns the sum of all color values
	def color_sum(self, step=1):
		w, h = self.im.size
		x_range = range( 0, w, step )
		y_range = range( 0, h, step )
		total = (0, 0, 0)
		px = self.im.load()
		for y in y_range:
			for x in x_range:
				color = px[x, y]
				try:
					total = tuple( map( sum, zip( total, color ) ) )
				except:
					if Config.debug:
						print( "error:", "color_sum:", "color:", color )
					pass
		return total

	def __text__(self, multiline=False, expected=3):
		if not multiline:
			return " ".join( pytesseract.image_to_string( self.im, lang='eng' ).split() )
		else:
			txt = pytesseract.image_to_string( self.im, lang='eng', config='-psm 3' ).splitlines()
			print("First Pass:", txt)
			if not txt and len( list( filter( None, txt ) ) ) != expected:
				# Try enhancing the image contrast
				contrast = ImageEnhance.Contrast( self.im )
				retry = contrast.enhance( 2 )
				retry = retry.convert( 'L' )
				txt = pytesseract.image_to_string( retry, lang='eng', config='-psm 3' ).splitlines()
				print( "Second Pass:", txt )
			if not txt and len( list( filter( None, txt ) ) ) != expected:
				# check for single character lines
				w, h = self.im.size
				count = 0
				for i in range( 0, int( h ), int( h / 3 ) ):
					if count >= 3:
						break
					box = (0, i, int( w / 2 ), i + int( h / 3 ))
					a = self.im.crop( box )
					ans = pytesseract.image_to_string( a, config='-psm 10' ).splitlines()
					if ans:
						txt.append( ans[0] )
						count += 1
			print( "Final:", txt )
			return list( filter( None, txt ) )

	def text(self, multiline=False, expected=3):
		async = pool.apply_async( self.__text__, (multiline, expected) )
		return async.get()

	# returns the index highlighted
	# TODO: allow check for different colors
	def selected(self, rows=3):
		w, h = self.im.size
		rh = int( floor( float( h ) / float( rows ) ) )
		sc = self.im.load()
		correct = -1
		green = [0, 0, 0]
		for i in range( rows ):
			for y in range( 0 + (i * rh), ((i + 1) * rh), 1 ):
				for x in range( 0, w, 1 ):
					color = sc[x, y]
					green[i] += color[1] - ((color[0] + color[2]) / 2)
			if Config.debug:
				print( "Question", i, "color:", green[i] )
			if i == 0 or green[i - 1] < green[i]:
				correct = i

		return correct

	def show(self):
		self.im.show()

	def write(self, file="test.png"):
		self.im.load()
		self.im.save( file )
