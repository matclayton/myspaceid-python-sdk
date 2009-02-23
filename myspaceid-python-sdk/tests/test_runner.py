#!/usr/bin/python

import unittest

class TestRunner(object):
  
  def __init__(self, modules_to_test=None):
    self.modules_to_test = modules_to_test or []
    
  def RunTests(self):
    runner = unittest.TextTestRunner()
    for module in self.modules_to_test:
      print '\nRunning tests in module', module.__name__
      runner.run(unittest.defaultTestLoader.loadTestsFromModule(module))