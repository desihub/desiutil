# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
==============
desiutil.timer
==============

Provides `Timer` class to standardize reporting of algorithm and I/O timing.

The `timer.Timer` class is intended for reporting timing of high-level events
that take seconds to minutes, e.g. reporting the timing for the input,
calculation, and output steps of a spectroscopic pipeline script.
It is *not* intended for detailed profiling of every possible function for
the purposes of optimization studies (use python cProfile for that);
nor is it intended for timing small functions deep in the call stack that
could result in N>>1 messages when run in parallel.

Example::

    from desiutil.timer import Timer
    t = Timer()
    t.start('blat')

    #- Use context manager for timing simple steps, e.g. one-liners
    with t.time('blat.input'):
        stuff = io.read(filename)

    #- Or use full start/stop if you prefer
    t.start('blat.algorithm')
    results = calculate(stuff)
    t.stop('blat.algorithm')

    with t.time('blat.output'):
        io.write(results)

    #- Stop outer timer; Note that named timers can be nested or interleaved
    t.stop('blat')

    #- Print a json report of the timing
    print(t.report())

This module has the philosophy that adding timing information should not
crash your code, even if the timer is used incorrectly, e.g. starting or
stopping a timer multiple times, stopping a timer that was never started,
or forgetting to stop a timer before asking for a report.  These print
additional warnings or error messages, but don't raise exceptions.
"""

import traceback
import time
import datetime
import json
import copy
import os.path
from contextlib import contextmanager

class Timer(object):
    """
    A basic timer class for standardizing reporting of algorithm and I/O timing
    
    TIMER:<START|STOP>:<filename>:<lineno>:<funcname>: <message>
    """
    
    def __init__(self):
        """
        Create a Timer object.

        Timing info is kept in `self.timers` dict

        timers[name]['start'] = start time (seconds since Epoch)
        timers[name]['start'] = stop time (seconds since Epoch)
        timers[name]['duration'] = stop - start (seconds)
        """
        self.timers = dict()
    
    def _prefix(self, step):
        """
        Return standard prefix string for timer reporting

        Args:
            step (str): timing step, e.g. "START" or "STOP"
        """
        stack = traceback.extract_stack()
        #- Walk backwards in stack to find first caller not from this file
        #- and not contextlib.py
        #- (exact index depends on whether context manager was used or not)
        thisfile = os.path.normpath(__file__)
        for caller in stack[-1::-1]:
            if os.path.normpath(caller.filename) != thisfile and \
               os.path.basename(caller.filename) != 'contextlib.py':
                break
        
        filename = os.path.basename(caller.filename)
        return f"TIMER-{step}:{filename}:{caller.lineno}:{caller.name}:"
    
    def start(self, name):
        """Start a timer `name` (str); prints TIMER-START message

        Args:
            name (str): name of timer to stop

        If `name` is started multiple times, the last call to `.start` is used
        for the timestamp.
        """
        # timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()        
        timestamp = datetime.datetime.now().isoformat()        
        if name in self.timers:
            print(self._prefix('WARNING'), f'Restarting {name} at {timestamp}')
        
        print(self._prefix('START'), f'Starting {name} at {timestamp}')
        # import desiutil.log
        # log = desiutil.log.get_logger()
        # log.info(f'Starting {name} at {timestamp}')
        self.timers[name] = dict(start=time.time())
    
    def stop(self, name):
        """Stop timer `name` (str); prints TIMER-STOP message

        Args:
            name (str): name of timer to stop

        Returns time since start in seconds, or -1.0 if `name` wasn't started

        Note: this purposefully does *not* raise an exception if called with
        a `name` that wasn't started, under the philosophy that adding timing
        statements shouldn't crash code, even if used incorrectly.

        If a timer is stopped multiple times, the final stop and duration
        are timestamped as the last call to `Timer.stop`.
        """
        #- non-fatal ERROR: trying to stop a timer that wasn't started
        timestamp = datetime.datetime.now().isoformat()        
        if name not in self.timers:
            print(self._prefix('ERROR'), f'Tried to stop non-existent timer {name} at {timestamp}')
            return -1.0

        #- WARNING: resetting the stop time of a timer that was already stopped
        if 'stop' in self.timers[name]:
            print(self._prefix('WARNING'), f'Resetting stop time of {name} at {timestamp}')
        
        #- All clear; proceed
        self.timers[name]['stop'] = time.time()
        dt = self.timers[name]['stop'] - self.timers[name]['start']
        self.timers[name]['duration'] = dt
        print(self._prefix('STOP'), f'Stopping {name} at {timestamp}; duration {dt:.2f} seconds')
        # import desiutil.log
        # log = desiutil.log.get_logger()
        # log.info(f'Stopping {name} at {timestamp}; duration {dt:.2f} seconds')
        return dt

    @contextmanager
    def time(self, name):
        """Context manager for timing a code snippet.

        Usage::

            t = Timer()
            with t.time('blat'):
                blat()

        is equivalent to::

            t = Timer()
            t.start('blat')
            blat()
            t.stop('blat')
        """
        self.start(name)
        try:
            yield
        finally:
            return self.stop(name)

    def timer_seconds2iso8601(self):
        """
        Return copy `self.timers` with start/stop as ISO-8601 strings

        Does *not* stop any running timers.
        """
        t = copy.deepcopy(self.timers)
        for name in t:
            for key in ['start', 'stop']:
                if key in t[name]:
                    iso8601 = datetime.datetime.fromtimestamp(t[name][key]).isoformat()
                    t[name][key] = iso8601

        return t

    def report(self):
        """
        Return a json dump of self.timers, with start/stop as ISO-8601 strings

        Implicitly stops any timers that are still running

        Use `Timer.timers` for access as a dictionary, where start/stop are
        seconds elapsed since the epoch (1970-01-01T00:00:00 UTC on Unix).
        """
        #- First stop any running timers
        for name in self.timers:
            if 'stop' not in self.timers[name]:
                self.stop(name)

        #- Get copy of self.timers converted to ISO-8601
        t = self.timer_seconds2iso8601()

        #- Convert to human-friendly formatted json string
        return json.dumps(t, indent=2)
        

