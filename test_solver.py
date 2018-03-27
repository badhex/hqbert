#!/usr/bin/env python3

from libs import solver_google

if __name__ == '__main__':
    question = "Ophthalmology is a branch of science dealing with which part of the body"
    answers = ("Eyes", "Feet", "Hands")
    solution = solver_google.solve(question, answers)
    print(solution)
