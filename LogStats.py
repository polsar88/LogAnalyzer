import apache_log_parser, calendar, multiprocessing, time
from collections import defaultdict, namedtuple
from datetime import datetime as dt
from threading import Lock
from watchdog.events import FileSystemEventHandler

from Alerter import Alerter
from Heap import Heap


# Codes for showing colored output.
C_OPEN = "\033["
C_CLOSE = "\033[0m"
GREEN = 32
RED = 31
MAGENTA = 35
def color(s, c):
    '''Returns the string s wrapped in control codes so that the terminal colors it c.'''
    return '%s1;%dm%s%s' % (C_OPEN, c, str(s), C_CLOSE)


# This defines a configuration for the program.
Config = namedtuple('Config', ('logFilePath', 'numHitsToGenAlert', 'alertWinLenSecs', 'useCurrTimestamps'))


class LogStats(FileSystemEventHandler):
    '''This class collects statistics on a watched log file. It also manages an Alerter object that creates (and silences) alerts when
    the site being monitors experiences high traffic.'''

    NUM_HIGHEST_TRAFFIC_SECTIONS_TO_SHOW = 3

    # https://en.wikipedia.org/wiki/Common_Log_Format
    # https://github.com/rory/apache-log-parser
    LOG_FORMAT = '%a %l %u %t "%m %U %H" %s %b'
    LOG_FORMAT_ALT = '%a %l %u %t "-" %s %b'  # In my experiments all log lines that failed the first format parsed using this one.

    # How to format datetime objects for printing.
    DATETIME_FMT = '%Y-%m-%d %H:%M:%S'


    def __init__(self, config):
        super().__init__()

        self.config = config

        # Open the log file for reading and seek to the end of it.
        self.logHandle = open(self.config.logFilePath)
        self.logHandle.seek(0, 2)

        # This parser is used to parse every log line.
        self.logParser = apache_log_parser.make_parser(LogStats.LOG_FORMAT)
        # If the first parser fails, we try this one.
        self.logParserAlt = apache_log_parser.make_parser(LogStats.LOG_FORMAT_ALT)

        # This lock grants exclusive access to data structures below.
        self.lock = Lock()

        # Various statistics.
        self.numHits = 0  # Total number of requests.
        self.numBadLines = 0  # Number of log lines that could not be parsed.
        self.responseBytesTot = 0  # Total response bytes sent.
        self.retCode2count = defaultdict(int)  # Count for each status code.
        self.method2count = defaultdict(int)  # Count for each request method.

        # This heap keeps track of all sections we have seen so far and their counts.
        self.heap = Heap()

        # Create the alerter and start its event loop in a separate process.
        self.alerter = Alerter(self.config.numHitsToGenAlert, self.config.alertWinLenSecs)
        self.alerterProc = multiprocessing.Process(target = self.alerter.runAlerter)
        self.alerterProc.start()


    def __del__(self):
        # Terminate the alerter process and wait for it to finish.
        self.alerterProc.terminate()
        self.alerterProc.join()

        self.logHandle.close()


    def __str__(self):
        '''Returns a formatted string showing various statistics and alerts.'''

        with self.lock:
            section2Count = self.heap.getMaxObjs(LogStats.NUM_HIGHEST_TRAFFIC_SECTIONS_TO_SHOW)
            ret = (color('SECTIONS WITH THE MOST HITS   : %s\n' % LogStats.getVal2CountStr(section2Count), GREEN) +
                         'Number of sections requested  : %d\n' % self.heap.getNumObjs() +
                         'Total number of hits          : %d\n' % self.numHits +
                         'Total response bytes          : %d\n' % self.responseBytesTot +
                         'Number of bad log lines       : %d\n' % self.numBadLines +
                         'Status code counts            : %s\n' % LogStats.getVal2CountStr(self.retCode2count) +
                         'Method counts                 : %s\n' % LogStats.getVal2CountStr(self.method2count))

        # Append alerts (if any). Alerter is thread-safe, so we don't need to have our lock acquired.
        for transition, tsSecs in self.alerter.getAlerts():
            if transition == 'EnterHigh':
                ret += color('High traffic generated an alert - hits >= %d, triggered at %s\n' %
                             (self.config.numHitsToGenAlert, dt.fromtimestamp(tsSecs).strftime(LogStats.DATETIME_FMT)), RED)
            elif transition == 'EnterLow':
                ret += color('High traffic alert recovered at %s\n' % dt.fromtimestamp(tsSecs).strftime(LogStats.DATETIME_FMT), MAGENTA)
            else:
                raise NotImplementedError('Unknown transition: "%s"' % str(transition))

        return ret


    @staticmethod
    def getVal2CountStr(val2count):
        '''Returns a nicely formatted representation of the passed dictionary.'''

        return ', '.join('%s: %d' % (str(val), count) for val, count in sorted(val2count.items(), reverse = True, key = lambda t: t[1]))


    def on_modified(self, event):
        '''This method gets called every time the directory containing our log file changes (as reported by the OS).'''

        super().on_modified(event)

        # Read all new lines in the log file and process each.
        for line in self.logHandle.readlines():
            line = line.strip()
            if len(line) > 0:
                self.processLogLine(line)


    def processLogLine(self, line):
        '''Parse the passed "line". If it cannot be parsed, the line is ignored.'''

        try:
            logTokens = self.logParser(line)
        except apache_log_parser.LineDoesntMatchException:
            # Try the other parser.
            try:
                logTokens = self.logParserAlt(line)
            except apache_log_parser.LineDoesntMatchException:
                with self.lock:
                    self.numBadLines += 1
                    return
        self.updateStats(logTokens)


    def updateStats(self, toks):
        '''Update our statistics based on the passed log line tokens.'''

        # Get the request timestamp.
        # https://github.com/rory/apache-log-parser
        # https://stackoverflow.com/questions/8777753/converting-datetime-date-to-utc-timestamp-in-python/8778548#8778548
        tsSecs = calendar.timegm(toks['time_received_utc_datetimeobj'].timetuple())
        self.alerter.addEvent(time.time() if self.config.useCurrTimestamps else tsSecs)  # Alerter has its own lock.

        # Extract the section. Find the second '/' and keep everything before it. If there is no second '/', keep everything.
        # This code is outside of critical section below since it doesn't require the lock to be held.
        if 'url_path' in toks:  # URL path will be missing if LOG_FORMAT_ALT was used to parse the log line.
            uri = toks['url_path']
            idx = uri.find('/', 1)  # Start searching after the first slash.
            section = uri if idx == -1 else uri[: idx]
            # Strip the query if present.
            idx = section.find('?')
            if idx != -1:
                section = section[ : idx]
        else:
            section = None

        with self.lock:
            if section is not None:
                # Update the heap.
                self.heap.addObj(section)

            # Update various stats.
            self.numHits += 1
            self.retCode2count[toks['status']] += 1
            if 'method' in toks:  # Method will be missing if LOG_FORMAT_ALT was used to parse the log line.
                self.method2count[toks['method']] += 1
            try:
                self.responseBytesTot += int(toks['response_bytes_clf'])
            except ValueError:
                # Raised if the string cannot be interpreted as an integer. In that case, it should be a '-'.
                pass
