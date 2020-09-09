# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.timer.
"""
import unittest
import json
import time
from ..timer import Timer

class TestTimer(unittest.TestCase):
    """Test desiutil.timer
    """

    def test_timer(self):
        """Basic timer functionality"""
        t = Timer()
        t.start('blat')

        #- Context manager is syntatic sugar for timing simple steps
        with t.time('blat.input'):
            time.sleep(0.1)

        #- Or use full start/stop
        t.start('blat.algorithm')
        time.sleep(0.1)
        t.stop('blat.algorithm')

        with t.time('blat.output'):
            time.sleep(0.1)

        #- Get timing report, which should be json parse-able
        timing_report = t.report()
        timing = json.loads(timing_report)

        for name in ['blat', 'blat.input', 'blat.algorithm', 'blat.output']:
            self.assertIn(name, timing.keys(), f'Missing timing report for name')
            self.assertIn('start', timing[name].keys(), f'{name} missing start time')
            self.assertIn('stop', timing[name].keys(), f'{name} missing stop time')
            self.assertIn('duration', timing[name].keys(), f'{name} missing duration')

        #- Subtests should approximately add up to wrapper test
        t0 = timing['blat']['duration']
        t1 = timing['blat.input']['duration'] + \
             timing['blat.algorithm']['duration'] + \
             timing['blat.output']['duration']

        self.assertAlmostEqual(t0, t1, 1)


    def test_timer_misuse(self):
        """Mis-use of timer should not be fatal"""
        t = Timer()

        #- Restarting a timer prints warning but isn't fatal
        t.start('blat')
        t.start('blat')

        #- Stopping a non-existing timer prints error but isn't fatal
        t.stop('foo')

        #- Stop a timer twice
        t.start('bar')
        t.stop('bar')
        t.stop('bar')

        #- Getting a report stops timers
        self.assertNotIn('stop', t.timers['blat'].keys())
        timing_report = t.report()
        self.assertIn('stop', t.timers['blat'].keys())


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m desiutil.test.test_timer
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
