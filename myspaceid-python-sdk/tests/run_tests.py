#!/usr/bin/python

import test_runner
import test_myspace_api

def RunTests():
  runner = test_runner.TestRunner()
  runner.modules_to_test = [test_myspace_api]
  runner.RunTests()

if __name__ == '__main__':
  RunTests()
