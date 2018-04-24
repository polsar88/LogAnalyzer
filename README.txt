RUNNING THE PROGRAM
-------------------

I have developed under Windows 10 with Anaconda distribution of Python 3.6.4. I cannot guarantee it will run in a lesser
version of Python. Additionally, I had to install the following two packages that are not part of Anaconda:

    pip install -U apache_log_parser
    pip install -U watchdog

I have included a sample log file (source.log) pulled from a real web server. This can be used to run the program
on real data. In order to use it, first run the main program like this (from THIS directory):

    python LogAnalyzerMain.py --logFilePath target.log --numHitsToGenAlert 10 --alertWinLenSecs 11 --useCurrTimestamps

I have chosen the CLI arguments in such a way as to make lots of alerts to be generated. Then run the program that reads
from source.log and writes lines into target.log with randomly chosen delay (between 0.5 and 1.5 seconds) to simulate
a real log file being written:

    python EmitLogLinesMain.py

If you want to run the program on a real log file being generated, choose the value of the first 3 CLI arguments accordingly
and OMIT THE "--useCurrTimestamps" ARGUMENT (this argument causes the alerter to use the current timestamp instead of the timestamp
recorded in the log line - the recorded timestamps are in the past and therefore otherwise no alerts would be generated).

You can run the alerter tests as follows:

    python AlerterTest.py

PLEASE EMAIL ME AT "polsar@gmail.com" IF YOU HAVE TROUBLE RUNNING THE PROGRAM IN ANY WAY :)


POTENTIAL DESIGN IMPROVEMENTS
-----------------------------
I ran out of time to satisfy the requirement to show the number of hits that generates a high-traffic alert. The alert is still
generated properly, but it doesn't show the exact number of hits (only that it is greater than or equal to the minimum required
to trigger the alert). So that would be the first thing I would implement.

I'd like to add more statistics to the output such as top remote IP addresses.

Adding the ability to parse Extended Log Format.

Instead of having the program run in a terminal, it would be cool to export the stats in an HTTP server and display all information
on a web page that automatically updates. A big project on its own! :)
