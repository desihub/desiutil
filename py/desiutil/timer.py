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
    
    def __init__(self, silent=False):
        """
        Create a Timer object.

        if `silent` is True, record timing but don't print log messages.

        Timing info is kept in `self.timers` dict

        timers[name]['start'] = start time (seconds since Epoch)
        timers[name]['start'] = stop time (seconds since Epoch)
        timers[name]['duration'] = stop - start (seconds)
        """
        self.timers = dict()
        self.silent = silent
    
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

    def _print(self, level, message):
        """Print message with timing level prefix if not `self.silent`

        Args:
           level (str): timing level ('START', 'STOP', 'WARNING', ...)
           message (str): message to print after standardized prefix
        """
        if not self.silent:
            print(self._prefix(level), message)

    def start(self, name, starttime=None):
        """Start a timer `name` (str); prints TIMER-START message

        Args:
            name (str): name of timer to stop

        Options:
            starttime (str or float): start time to use instead of now

        If `name` is started multiple times, the last call to `.start` is used
        for the timestamp.

        Tries to parse `starttime` in this order:

            1. (float) Unix time-since epoch
            2. (str) ISO-8601
            3. (str) Unix `date` cmd, e.g. "Mon Sep 21 20:09:48 PDT 2020"
        """
        starttime = parsetime(starttime)
        isotime = datetime.datetime.fromtimestamp(starttime).isoformat()
        if name in self.timers:
            self._print('WARNING', f'Restarting {name} at {isotime}')
        
        self._print('START', f'Starting {name} at {isotime}')
        self.timers[name] = dict(start=starttime)
    
    def stop(self, name, stoptime=None):
        """Stop timer `name` (str); prints TIMER-STOP message

        Args:
            name (str): name of timer to stop

        Options:
            stoptime (str or float): stop time to use instead of now

        Returns time since start in seconds, or -1.0 if `name` wasn't started

        Note: this purposefully does *not* raise an exception if called with
        a `name` that wasn't started, under the philosophy that adding timing
        statements shouldn't crash code, even if used incorrectly.

        If a timer is stopped multiple times, the final stop and duration
        are timestamped as the last call to `Timer.stop`.

        Tries to parse `stoptime` in this order:

            1. (float) Unix time-since epoch
            2. (str) ISO-8601
            3. (str) Unix `date` cmd, e.g. "Mon Sep 21 20:09:48 PDT 2020"
        """
        #- non-fatal ERROR: trying to stop a timer that wasn't started
        stoptime = parsetime(stoptime)
        isotime = datetime.datetime.fromtimestamp(stoptime).isoformat()
        if name not in self.timers:
            self._print('ERROR', f'Tried to stop non-existent timer {name} at {isotime}')
            return -1.0

        #- WARNING: resetting the stop time of a timer that was already stopped
        if 'stop' in self.timers[name]:
            self._print('WARNING', f'Resetting stop time of {name} at {isotime}')
        
        #- All clear; proceed
        self.timers[name]['stop'] = stoptime
        dt = self.timers[name]['stop'] - self.timers[name]['start']
        self.timers[name]['duration'] = dt
        self._print('STOP', f'Stopping {name} at {isotime}; duration {dt:.2f} seconds')
        return dt

    def stopall(self):
        """Stop any timers that have not yet been individually stopped"""
        for name in self.timers:
            if 'stop' not in self.timers[name]:
                self.stop(name)

    def cancel(self, name):
        """Cancel timer `name` and remove from timing log"""
        t1 = time.time()
        isotime = datetime.datetime.fromtimestamp(t1).isoformat()
        if name in self.timers:
            dt = t1 - self.timers[name]['start']
            print(self._prefix('CANCEL'), f'Canceling timer {name} at {isotime} after {dt:.2f} seconds')
            del self.timers[name]
        else:
            print(self._prefix('WARNING'), f'Attempt to cancel non-existent timer {name} at {isotime}')

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
                    isotime = timestamp2isotime(t[name][key])
                    t[name][key] = isotime

        return t

    def report(self):
        """
        Return a json dump of self.timers, with start/stop as ISO-8601 strings

        Implicitly stops any timers that are still running

        Use `Timer.timers` for access as a dictionary, where start/stop are
        seconds elapsed since the epoch (1970-01-01T00:00:00 UTC on Unix).
        """
        #- First stop any running timers
        self.stopall()

        #- Get copy of self.timers converted to ISO-8601
        t = self.timer_seconds2iso8601()

        #- Convert to human-friendly formatted json string
        return json.dumps(t, indent=2)
        

#-----
#- Utility functions

def timestamp2isotime(timestamp):
    """Return seconds since epoch `timestamp` as ISO-8601 string
    """
    return datetime.datetime.fromtimestamp(timestamp).isoformat()

def parsetime(t):
    """Parse time as int,float,str(int),str(float),ISO-8601, or Unix `date`

    If `t` is None, return `time.time()`

    Returns `t` as float Unix seconds since epoch timestamp
    """
    if t is None:
        return time.time()
    elif isinstance(t, (float, int)):
        return float(t)
    elif isinstance(t, str):
        try:
            #- int or float passed in as string
            t = float(t)
        except ValueError:
            #- see if dateutil is installed to parse
            #- ISO-8601 string, or output of Unix `date` without options
            try:
                import dateutil.parser
            except ImportError:
                raise ValueError(f"Can't parse start time {t}; " \
                                  "install dateutil or use int/float " \
                                  "(e.g. from Unix `date +%s`")

            try:
                t = dateutil.parser.parse(t).timestamp()
            except:
                raise ValueError(f"Can't parse start time {t}; " \
                                  "use int/float or ISO-8601 or " \
                                  "Unix `date` output")

    return t

def compute_stats(timerlist):
    """Compute timer min/max/mean/median stats

    Args:
        timerlist: list of Timer objects

    Returns: dict[timername][...] with keys
    for start/stop/duration.min/max/mean/median

    Different Timers can have different named subtimers
    """

    #- Minimize timer import time by loading numpy only if needed
    import numpy as np

    #- Result dictionary to fill
    stats = dict()

    #- Extract timers dictionaries
    timerlist = [t.timers for t in timerlist]

    #- Get the name of all individual timers in the list of timers
    #- while retaining order of first appearance
    names = dict()
    for t in timerlist:
        for n in t.keys():
            names[n] = 1
    names = list(names.keys()) # cPy3.6 and any py3.7 preserves key order

    for name in names:
        duration = list()
        start = list()
        stop = list()
        for t in timerlist:
            if name in t:
                if 'duration' in t[name]:
                    duration.append(t[name]['duration'])
                    start.append(t[name]['start'])
                    stop.append(t[name]['stop'])

        duration = np.array(duration)
        start = np.array(start)
        stop = np.array(stop)
        stats[name] = {
            'start.min': timestamp2isotime(np.min(start)),
            'start.max': timestamp2isotime(np.max(start)),
            'start.mean': timestamp2isotime(np.mean(start)),
            'start.median': timestamp2isotime(np.median(start)),
            'stop.min': timestamp2isotime(np.min(stop)),
            'stop.max': timestamp2isotime(np.max(stop)),
            'stop.mean': timestamp2isotime(np.mean(stop)),
            'stop.median': timestamp2isotime(np.median(stop)),
            'duration.min': np.min(duration),
            'duration.max': np.max(duration),
            'duration.mean': np.mean(duration),
            'duration.median': np.median(duration),
            'n': len(duration),
            }

    return stats

