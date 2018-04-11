#!/usr/bin/env python3

# from libs.adb_reader import HQscreen
import uiautomator2 as u2


if __name__ == '__main__':
	# screen = HQscreen()
	# screen.save_xml()
	d = u2.connect_usb('00e4fdeeb8cfbecc')
	print(d.info)



