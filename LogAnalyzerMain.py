import argparse

from LogAnalyzer import LogAnalyzer
from LogStats import Config


# Default alerting parameters. Both can be overriden using CLI arguments.
NUM_HITS_TO_GENERATE_ALERT = 110
TIME_WINDOW_TO_GENERATE_ALERT_SECS = 2 * 60  # 2 minutes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logFilePath', required = True, type = str,
                        help = 'The log file path to be monitored.')
    parser.add_argument('--numHitsToGenAlert', required = False, type = int, default = NUM_HITS_TO_GENERATE_ALERT,
                        help = 'The number of hits within alerting window required to generate alert.')
    parser.add_argument('--alertWinLenSecs', required = False, type = int, default = TIME_WINDOW_TO_GENERATE_ALERT_SECS,
                        help = 'The length of the alerting window in seconds.')
    parser.add_argument('--useCurrTimestamps', action = 'store_true',
                        help = 'Use current timestamp instead of logged timestamp when generating alerts.')
    args = parser.parse_args()

    analyzer = LogAnalyzer(Config(
        logFilePath           = args.logFilePath,
        numHitsToGenAlert     = args.numHitsToGenAlert,
        alertWinLenSecs       = args.alertWinLenSecs,
        useCurrTimestamps     = args.useCurrTimestamps,
    ))
    analyzer.runForever()


if __name__ == '__main__':
    main()
