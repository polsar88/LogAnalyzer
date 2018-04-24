import bisect, multiprocessing, time


class Alerter:

    # We check for state change every this many seconds.
    SAMPLING_DELAY_SECS = 1


    def __init__(self, minNumEvents, winLenSecs):
        '''We create a "High" alert if at least "minNumEvents" occur within the last "winLenSecs" seconds.
        The alert is silenced when this condition no longer holds true.'''

        self.minNumEvents, self.winLenSecs = minNumEvents, winLenSecs

        # Since we need to share the variables below between 2 processes, we need to use a Manager object to create proxies for them.
        # https://docs.python.org/3.6/library/multiprocessing.html#managers
        manager = multiprocessing.Manager()

        # This lock grants exclusive access to the variables below.
        self.lock = manager.Lock()

        self.tss = manager.list([])  # Circular array of length at most "self.minNumEvents".
        self.idx = manager.Value(int, 0)  # The current start index in "self.tss".
        # We start in "Low" state. We transition to "High" state if at least "self.minNumEvents" events happen within last "self.winLenSecs".
        self.state = manager.Value(str, 'Low')

        # This is a chronologically ordered list of tuples (transition, tsSecs), where "transition" is either "EnterHigh" for a Low -> High transition,
        # or "EnterLow" for the opposite. "tsSecs" is the timestamp in seconds when the transition occurred. This list is returned and then a new empty
        # list is started by calling "getAlerts()" method.
        #
        # We cannot use ListProxy here like we do for "self.tss", because a ListProxy object cannot be cleared efficiently.
        # Creating a new ListProxy would work, but then "manager" would need to be an instance variable, which doesn't work because it is not pickable.
        # This is a recently reported bug: https://bugs.python.org/issue33088
        self.alerts = manager.Value(list, [])


    def addEvent(self, tsSecs):
        '''Adds event with the passed timestamp.'''

        with self.lock:
            if len(self.tss) > 0:
                # The series should be monotonically increasing. If the new timestamp is before the last timestamp, clock skew may have played a part,
                # so we clip it to the last timestamp.
                tsSecsPrev = self.tss[self.idx.value - 1]  # If "self.idx == 0", the previous timestamp is at "self.tss[-1]".
                tsSecs = tsSecs if tsSecsPrev <= tsSecs else tsSecsPrev

            if len(self.tss) < self.minNumEvents:
                # We haven't reached the required number of timestamps yet.
                self.tss.append(tsSecs)
            else:
                assert len(self.tss) == self.minNumEvents
                # Overwrite the earliest timestamp we have and make it the new end of the list.
                self.tss[self.idx.value] = tsSecs
                self.idx.set((self.idx.value + 1) % self.minNumEvents)


    def runAlerter(self):
        '''This method runs the alerter. It does not return and should be run in a separate thread.'''

        while True:
            time.sleep(Alerter.SAMPLING_DELAY_SECS)
            with self.lock:
                self.genAlert()


    def genAlert(self):
        '''Generates an alert If the number of events in the sliding window crosses the alerting threshold.
        This method assumes the caller has acquired the lock.'''

        if len(self.tss) < self.minNumEvents:
            # Not enough events yet.
            return

        # Determine whether or not all timestamps occur on or after the timestamp corresponding to the beginning of our window.
        # https://docs.python.org/3.6/library/bisect.html
        currSecs = time.time()
        winStartSecs = currSecs - self.winLenSecs
        if bisect.bisect_left(self.tss, winStartSecs, self.idx.value) != self.idx.value:
            # If we are in the "High" state, we need to transition to the "Low" state. Otherwise, we don't need to do anything.
            if self.state.value == 'High':
                lst = self.alerts.value
                lst.append(('EnterLow', currSecs))
                self.alerts.set(lst)
                self.state.set('Low')
        elif self.idx.value == 0 or bisect.bisect_left(self.tss, winStartSecs, 0, self.idx.value - 1) == 0:
            # If we are in the "Low" state, we need to transition to the "High" state. Otherwise, we don't need to do anything.
            if self.state.value == 'Low':
                lst = self.alerts.value
                lst.append(('EnterHigh', currSecs))
                self.alerts.set(lst)
                self.state.set('High')


    def getAlerts(self):
        '''Returns tuples (transition, tsSecs) indicating "EnterHigh" or "EnterLow" transitions and the timestamp of their occurrence
        since the last time this method was called.'''

        with self.lock:
            ret = self.alerts.value
            self.alerts.set([])
        return ret
