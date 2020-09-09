"""
timer: standardizing reporting of algorithm and I/O timing

The `timer.Timer` class is intended for reporting timing of events that
take seconds to minutes; it is not intended for detailed profiling.  Example::

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
        """Start a timer `name` (str)"""
        # timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()        
        timestamp = datetime.datetime.now().isoformat()        
        if name in self.timers:
            print(self._prefix('WARNING'), f'Restarting {name} at {timestamp}')
        
        print(self._prefix('START'), f'Starting {name} at {timestamp}')
        self.timers[name] = dict(start=time.time())
    
    def stop(self, name):
        """Stop timer `name` (str)"""
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
        return dt

    @contextmanager
    def time(self, name):
        self.start(name)
        try:
            yield
        finally:
            return self.stop(name)

    def report(self):
        """
        Return a json dump of self.timers, with start/stop as ISO-8601 strings
        
        Implicitly stops any timers that are still running
        """
        #- First stop any running timers
        for name in self.timers:
            if 'stop' not in self.timers[name]:
                self.stop(name)
        
        #- Now replace time-since-epoch float with ISO-8601 str using copy
        t = copy.deepcopy(self.timers)
        for name in t:            
            for key in ['start', 'stop']:
                tx = datetime.datetime.fromtimestamp(t[name][key]).isoformat()
                t[name][key] = tx

        return json.dumps(t, indent=2)
        

