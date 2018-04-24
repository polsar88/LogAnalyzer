import os, random, time

def main():
    with open('source.log') as f:
        lines = f.readlines()

    with open('target.log', 'a+') as f:
        for line in lines:
            f.write(line)
            f.flush()
            # Signal the OS that the file has changed.
            # https://stackoverflow.com/a/608518/904272
            os.fsync(f.fileno())
            print(line.strip())
            # This results in a new log line to be written to the target file every 1 second ON AVERAGE.
            time.sleep(random.uniform(0.5, 1.5))

if __name__ == '__main__':
    main()
