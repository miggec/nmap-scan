import os
import subprocess
import datetime
from time import sleep
import sys

print("Usage: python jtrack.py [known_device] [stime]")


def device_connected(device: str):
    ip_scan = str(subprocess.check_output("nmap -sn 192.168.0.0/24", shell=True))
    if ip_scan.__contains__(device):
        return True
    else:
        return False


def scan_home(device: str, stime=int(sys.argv[2])):
    """
    Scans the network for a certain device
    Yields the connect and disconnect times at a time interval defined in seconds by stime
    Also yields the time last spent connected if the device has just disconnected

    :param device: device name to scan for
    :param stime: sleep time between scan attempts
    :return:
    """

    already_connected = False
    connect_ts = None
    disconnect_ts = None
    time_spent_connected = None

    while True:

        if device_connected(device):

            if not already_connected:  # just reconnected

                # TODO check if false alarm? some spurious results happening

                event = "Reconnected"

                # Calculate time spent disconnected and reset the disconnect timestamp
                connect_ts = datetime.datetime.now()
                try:
                    time_delta = (connect_ts - disconnect_ts).total_seconds()
                    time_spent_disconnected = str(datetime.timedelta(seconds=int(time_delta)))
                except TypeError:
                    time_spent_disconnected = None
                disconnect_ts = None

                already_connected = True
                print("Connected at", connect_ts)
                print("Time spent connected:", time_spent_connected)

                yield scan_result(connect_ts, time_spent_connected, disconnect_ts, time_spent_disconnected, event)

            if already_connected:  # remains connected_status
                pass

        else:
            if already_connected:  # just disconnected?
                false_alarm = False
                possible_disconnect_time = datetime.datetime.now()  # save this time now, to report accurately later

                for i in range(10):  # retries to be sure TODO a value of 10 seems sensible
                    if device_connected(device):
                        false_alarm = True
                        break
                    elif not device_connected(device):
                        sleep(10)  # TODO decrease for testing

                if not false_alarm:
                    event = "Disconnected"
                    disconnect_ts = possible_disconnect_time
                    time_delta = (disconnect_ts - connect_ts).total_seconds()
                    time_spent_connected = str(datetime.timedelta(seconds=int(time_delta)))
                    time_spent_disconnected = None
                    connect_ts = None

                    print("Disconnected at", disconnect_ts)
                    print("Time spent connected:", time_spent_connected)

                    already_connected = False

                    yield scan_result(connect_ts, time_spent_connected, disconnect_ts, time_spent_disconnected, event)

            elif not already_connected:  # remains disconnected
                time_spent_connected = None

        sleep(stime)


def scan_result(connect_ts, time_spent_connected, disconnect_ts, time_spent_disconnected, event):

    try:
        connect_time_str = connect_ts.isoformat(sep=" ")  # timespec='minutes') <-- Python 3.6 only...
    except AttributeError:
        connect_time_str = None
    try:
        disconnect_time_str = disconnect_ts.isoformat(sep=" ")  # timespec='minutes')
    except AttributeError:
        disconnect_time_str = None

    time_stamp = datetime.datetime.now().isoformat(sep=" ")  # timespec='seconds')

    return [time_stamp, event, connect_time_str, time_spent_disconnected, disconnect_time_str, time_spent_connected]


def track_device(device):

    filename_time_stamp = datetime.datetime.now().strftime("_%d-%b-%a_%H-%M-%S")
    csv_file_name = device + filename_time_stamp + ".csv"

    with open(csv_file_name, 'w', encoding='utf-8') as outfile:
        outfile.write("time_stamp, event, connect_ts, time_spent_disconnected, disconnect_ts, time_spent_connected,\n")

    while True:
        for scan in scan_home('android-fc090a3a8a86db64'):
            with open(csv_file_name, 'a', encoding='utf-8') as append_file:
                    for column in scan:
                        append_file.write(str(column) + ",")
                    append_file.write("\n")

            # TODO test this works during internet outage
            commit_ts = datetime.datetime.now().strftime("%a-%d-%b_%H-%M-%S")
            try:
                commit_to_git(commit_ts, csv_file_name)
            except Exception as e:
                print(commit_ts)
                print("\nGit commit failed with error:\n" + str(e) + "\n\nWill re-attempt at next event")


def commit_to_git(filename_time_stamp, file_to_commit):
    """
    Should probably use the developer API for this!

    :param filename_time_stamp:
    :return:
    """
    os.system("git add " + file_to_commit)
    commit_command = 'git commit -m " autocommit @ ' + filename_time_stamp + '"'
    os.system(commit_command)
    os.system("git push -u origin master")


track_device(sys.argv[1])

# android-9b72272b83db0551 = C
# android-fc090a3a8a86db64 = M
# android-a7226cbab44b68c5 = J
