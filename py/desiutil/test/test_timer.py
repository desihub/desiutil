# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.timer.
"""
import unittest
import json
import time
from ..timer import Timer, compute_stats, parsetime

dateutil_installed = False
try:
    import dateutil
    dateutil_installed = True
except ImportError:
    pass

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

    def test_cancel(self):
        """Test canceling a timer"""
        t = Timer()
        t.start('blat')
        t.start('foo')
        self.assertIn('blat', t.timers)
        self.assertIn('foo', t.timers)
        t.cancel('foo')
        self.assertIn('blat', t.timers)
        self.assertNotIn('foo', t.timers)

        #- Non-fatal to cancel a non-existent timer
        t.cancel('quat')

    def test_stopall(self):
        """Test stopping a batch of timers"""

        t = Timer()
        t.start('blat')
        t.start('foo')
        t.start('bar')

        t.stop('blat')
        self.assertIn('stop', t.timers['blat'].keys())
        self.assertNotIn('stop', t.timers['foo'].keys())
        self.assertNotIn('stop', t.timers['bar'].keys())

        t.stopall()
        self.assertIn('stop', t.timers['blat'].keys())
        self.assertIn('stop', t.timers['foo'].keys())
        self.assertIn('stop', t.timers['bar'].keys())

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

    def test_parsetime(self):
        """Test parsing timestamps as int, float, or string"""
        t0 = parsetime(1600807346)
        t1 = parsetime(1600807346.0)
        t2 = parsetime("1600807346")
        t3 = parsetime("1600807346.0")
        self.assertAlmostEqual(t0, 1600807346.0)
        self.assertAlmostEqual(t0, t1)
        self.assertAlmostEqual(t0, t2)
        self.assertAlmostEqual(t0, t3)

        timer = Timer()
        timer.start('blat', starttime=1600807346)
        timer.stop('blat', stoptime=1600807346+2)
        self.assertAlmostEqual(timer.timers['blat']['start'], 1600807346.0)
        self.assertAlmostEqual(timer.timers['blat']['duration'], 2)

    @unittest.skipUnless(dateutil_installed, "dateutil not installed")
    def test_parsetime_dateutil(self):
        """If dateutil installed, test ISO-8601 date string parsing

        Fancier "Tue Sep 22 13:42:26 PDT 2020" parsing may or may not
        work depending upon timezone knowledge of host machine; not
        tested or supported for now, but may be re-added later if needed.
        """
        # t0 = parsetime("Tue Sep 22 13:42:26 PDT 2020")
        # self.assertAlmostEqual(t0, 1600807346.0)
        t1 = parsetime("2020-09-22T13:42:26-07:00")
        self.assertAlmostEqual(t1, 1600807346.0)

        with self.assertRaises(ValueError):
            t2 = parsetime("My Birthday")

    @unittest.skipIf(dateutil_installed, "dateutil installed")
    def test_parsetime_no_dateutil(self):
        """If dateutil not installed, confirm failure modes"""
        # with unittest.assertRaises(ValueError):
        #     t0 = parsetime("Tue Sep 22 13:42:26 PDT 2020")
        with unittest.assertRaises(ValueError):
            t1 = parsetime("2020-09-22T13:42:26-07:00")

    def test_stats(self):
        """Test generating summary statistics for a list of Timers"""
        t1 = Timer()
        t2 = Timer()
        t3 = Timer()

        t1.start('blat')
        time.sleep(0.01)
        t2.start('blat')
        time.sleep(0.01)
        t3.start('blat')
        time.sleep(0.01)

        t1.start('foo')
        time.sleep(0.01)
        t2.start('foo')
        time.sleep(0.01)

        t2.start('bar')
        time.sleep(0.01)
        t3.start('bar')
        time.sleep(0.01)

        t1.stopall()
        t2.stopall()
        t3.stopall()

        stats = compute_stats([t1,t2,t3])

        self.assertEqual(stats['blat']['n'], 3)
        self.assertEqual(stats['foo']['n'], 2)
        self.assertEqual(stats['bar']['n'], 2)

        for name, s in stats.items():
            for key in ['start', 'stop', 'duration']:
                self.assertLess(s[f'{key}.min'], s[f'{key}.mean'])
                self.assertLess(s[f'{key}.min'], s[f'{key}.median'])
                self.assertLess(s[f'{key}.mean'], s[f'{key}.max'])

def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m desiutil.test.test_timer
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
