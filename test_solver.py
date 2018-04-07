#!/usr/bin/env python3

from libs import solver_google

if __name__ == '__main__':
	question = "Which pair of countries can be found on the Horn of Africa?"
	answers = ("Egypt / Ethiopia", "Ethiopia / Eritrea", "Eritrea / Egypt")
	solution = solver_google.solve( question, answers )
	print( solution )
