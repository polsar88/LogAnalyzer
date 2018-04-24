import os, time

from watchdog.observers import Observer

from LogStats import LogStats

class LogAnalyzer:
    '''This class contains an event loop that outputs log analysis statistics at regular intervals.'''

    OUTPUT_DELAY_SECS = 10


    def __init__(self, config):
        '''Once "runForever()" method is called, the log file specified by "config.logFilePath" will be actively consumed
        and various statistics output to stdout at regular intervals. If "config.useCurrTimestamps" is True, we use current
        timestamp instead of the logged request timestamp for the purposes of generating high-traffic alerts. This is useful
        when running the analyzer on a test log file that has timestamps way in the past.'''

        self.config = config


    def runForever(self):
        '''Starts the main event loop. It never returns.'''

        stats = LogStats(self.config)

        # Create and start the observer that will watch for changes in the directory in which the log file is located.
        observer = Observer()
        observer.schedule(stats, LogAnalyzer.getDirPath(self.config.logFilePath), recursive = False)
        observer.start()

        try:
            # Output stats at regular intervals.
            while True:
                time.sleep(LogAnalyzer.OUTPUT_DELAY_SECS)
                print(str(stats))
        finally:
            # Do not leave the observer thread hanging around.
            observer.stop()
            observer.join()


    @staticmethod
    def getDirPath(filePath):
        '''Returns the directory path for the passed file path.'''

        dirPath = os.path.dirname(filePath)
        # "os.path.dirname()" returns '' if "filePath" is just the file name.
        return '.' if len(dirPath) == 0 else dirPath
