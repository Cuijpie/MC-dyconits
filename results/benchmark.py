import psutil
import os
import threading
import random
import time
from datetime import datetime
import csv
import subprocess
import sys
from fabric import Connection

class Benchmark(threading.Thread):
    def __init__(self):
        self.running = False
        self.benchmark = {}
        threading.Thread.__init__(self)

    def run(self):
        self.running = True
        self.benchmark["time"] = []
        self.benchmark["net_packet"] = []
        self.benchmark["net_bytes"] = []
        self.benchmark["cpu"] = []
        self.benchmark["mem"] = []
        self.benchmark["disk_read"] = []
        self.benchmark["disk_write"] = []
        self.benchmark["interrupts"] = []
        self.benchmark["usermode"] = []
        self.benchmark["kernelmode"] = []
        self.benchmark["iowait"] = []
        time_counter = 0

        process = psutil.Process(17875)  # PID of Opencraft instance that is running.

        while self.running:
            # Collect T1
            io_counter_t1 = psutil.net_io_counters()
            disk_counter_t1 = psutil.disk_io_counters()
            interrupts_t1 = psutil.cpu_stats()
            cputimes_t1 = process.cpu_times()

            # wait a second
            time.sleep(1)
            time_counter += 1

            # Collect T2
            io_counter_t2 = psutil.net_io_counters()
            disk_counter_t2 = psutil.disk_io_counters()
            interrupts_t2 = psutil.cpu_stats()
            cputimes_t2 = process.cpu_times()

            # Additional metric
            cpu_usage = process.cpu_percent()
            mem_usage = process.memory_percent()
            #ct = process.cpu_times()  
            # Compute deltas
            packets_sent = io_counter_t2.packets_sent - io_counter_t1.packets_sent
            bytes_sent = io_counter_t2.bytes_sent - io_counter_t1.bytes_sent
            bytes_write = disk_counter_t2.write_bytes - disk_counter_t1.write_bytes
            bytes_read = disk_counter_t2.read_bytes - disk_counter_t1.read_bytes
            bytes_write = disk_counter_t2.write_bytes - disk_counter_t1.write_bytes
            interrupts = interrupts_t2.interrupts - interrupts_t1.interrupts
            usermode = cputimes_t2.user - cputimes_t1.user
            kernelmode = cputimes_t2.system - cputimes_t1.system
            iowait = cputimes_t2.iowait - cputimes_t1.iowait

            # Add to benchmark session
            self.benchmark["time"].append(time_counter)
            self.benchmark["net_packet"].append(packets_sent)
            self.benchmark["net_bytes"].append(bytes_sent)
            self.benchmark["cpu"].append(cpu_usage)
            self.benchmark["mem"].append(mem_usage)
            self.benchmark["disk_read"].append(bytes_read)
            self.benchmark["disk_write"].append(bytes_write)
            self.benchmark["interrupts"].append(interrupts)
            self.benchmark["usermode"].append(usermode)
            self.benchmark["kernelmode"].append(kernelmode)
            self.benchmark["iowait"].append(iowait)
            print("------------------------------------")
            print(datetime.now().strftime("%H:%M:%S"))
            print("Packets sent: " + str(packets_sent))
            print("Bytes sent: " + str(bytes_sent))
            print("cpu usage: " + str(cpu_usage))
            print("mem usage: " + str(mem_usage))
            print("bytes read: " + str(bytes_read))
            print("bytes write: " + str(bytes_write))
            print("interrupts: " + str(interrupts))
            print("time in usermode: " + str(usermode))
            print("time in kernelmode: " + str(kernelmode))
            print("time in iowait: " + str(iowait))

    def stop(self):
        self.running = False
        csv_file = "<prefix-name-file>" + str(datetime.now().strftime("%H%M%S")) + ".csv"

        try:
            with open(csv_file, 'w') as csvfile:
                writer = csv.writer(csvfile)
                for key, value in self.benchmark.items():
                    writer.writerow([key, value])

            csvfile.close()

        except IOError:
            print("I/O error")



def main():
    p = Connection(sys.argv[1]) # DAS-5 specific: give machine ID where yardstick is located.

    for i in range(20):
        bm = Benchmark()
        experiment = i + 1
        print("EXPERIMENT: " + str(experiment) + " START...")
        
        p.run("cd <path/to/yardstick> && (nohup java -jar target/yardstick-1.0.1-jar-with-dependencies.jar \
         -e <experiment> -h <host> -Ebots=<number of bots> -Eduration=<duration of experiment> &> /dev/null < /dev/null &) && /bin/true")

        print("DEPLOY BOTS...")
        
        time.sleep(540)
        
        print("START BENCHMARK...")

        bm.start()
        
        time.sleep(60)
        
        print("STOP BENCHMARK...")
        
        bm.stop()
        p.run("pkill java")
        del bm

if __name__ == "__main__":
    main()
