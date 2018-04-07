#!/usr/bin/env python3

from libs.adb_reader import HQscreen


if __name__ == '__main__':
	screen = HQscreen()
	screen.save_xml()


