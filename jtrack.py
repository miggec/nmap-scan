import os
import subprocess
import datetime
from time import sleep
import sys


def device_connected(device: str):
    """
    True/False - is 'device' seen on the network?
    :param device: device name as returned by nmap
    :return: bool
    """
    return device in str(subprocess.check_output("nmap -sn 192.168.0.0/24", shell=True))


def scan_home(device: str, stime):
    """
    Scans the network for a certain device
    Yields the connect and disconnect times at a time interval defined in seconds by stime
    Also yields the time last spent connected if the device has just disconnected
    Checks for false alarm if disconnect detected, makes sure before reporting
    Only reports 'reconnected' if disconnected for more than 2 minutes - otherwise no event happens

    :param device: device name to scan for
    :param stime: sleep time between scan attempts
    :return:
    """

    currently_connected = False
    connect_ts = None
    disconnect_ts = None

    while True:

        if device_connected(device) and not currently_connected:  # just reconnected

            event = "Reconnected"

            # Calculate time spent disconnected and reset the disconnect timestamp
            connect_ts = datetime.datetime.now()

            try:
                time_delta_seconds = (connect_ts - disconnect_ts).total_seconds()
                time_spent_disconnected = str(datetime.timedelta(seconds=int(time_delta_seconds)))
            except TypeError:
                time_spent_disconnected = None
                time_delta_seconds = 0

            disconnect_ts = None
            if time_delta_seconds > 90 or time_delta_seconds == 0:  # ignore temporary dropouts
                currently_connected = True

            print("Connected at", connect_ts)
            print("Time spent disconnected:", time_spent_disconnected)
            time_spent_connected = None

            if time_delta_seconds == 0 and not disconnect_ts:
                event = "Currently connected"
                currently_connected = True

            if currently_connected:
                yield scan_result(connect_ts, time_spent_connected, time_spent_disconnected, event)

        elif not device_connected(device) and currently_connected:  # just disconnected?

            # Record timestamp before assessing for false alarm / very short disconnect
            possible_disconnect_time = datetime.datetime.now()
            false_alarm = False

            for i in range(8):
                if device_connected(device):
                    false_alarm = True
                else:
                    sleep(15)

            if not false_alarm:
                event = "Disconnected"

                disconnect_ts = possible_disconnect_time
                time_delta_seconds = (disconnect_ts - connect_ts).total_seconds()
                time_spent_connected = str(datetime.timedelta(seconds=int(time_delta_seconds)))

                time_spent_disconnected = None
                connect_ts = None

                print("Disconnected at", disconnect_ts)
                print("Time spent connected:", time_spent_connected)

                currently_connected = False

                yield scan_result(disconnect_ts, time_spent_connected, time_spent_disconnected, event)

        elif not device_connected(device) and not disconnect_ts:

            event = "Currently disconnected"
            disconnect_ts = datetime.datetime.now()
            print("Disconnected at", disconnect_ts)
            time_spent_connected = None
            time_spent_disconnected = None
            yield scan_result(disconnect_ts, time_spent_connected, time_spent_disconnected, event)

        sleep(stime)


def scan_result(event_ts, time_spent_connected, time_spent_disconnected, event):
    """
    Formats timestamps and returns a row ready to be written to a results CSV

    :param event_ts: datetime
    :param time_spent_connected: datetime.timedelta
    :param time_spent_disconnected: datetime.timedelta
    :param event: string descriptor of event
    :return: results list
    """
    event_time_str = event_ts.strftime("%a %d %b %H:%M")
    time_stamp = datetime.datetime.now().isoformat(sep=" ")[:-7]

    print("Event: ", [time_stamp, event, event_time_str, time_spent_disconnected, time_spent_connected])
    return [time_stamp, event, event_time_str, time_spent_disconnected, time_spent_connected]


def track_device(device, device_alias):
    """

    :param device: device name on the network, e.g. "Mums-iPhone"
    :param device_alias: Human alias for the device, nice to have if device name is gibberish. Used for CSV filename.
    :return: Calls the scan_home function, writes results to CSV and pushes to github
    """

    if not device_alias:
        device_alias = device

    filename_time_stamp = datetime.datetime.now().strftime("_%d-%b-%a_%H-%M-%S")
    csv_file_name = device_alias + filename_time_stamp + ".csv"

    with open(csv_file_name, 'w', encoding='utf-8') as outfile:
        outfile.write("time_stamp, event, event_ts, time_spent_disconnected, time_spent_connected,\n")

    while True:
        for scan in scan_home(device, sleep_time):
            with open(csv_file_name, 'a', encoding='utf-8') as append_file:
                    for column in scan:
                        append_file.write(str(column) + ",")
                    append_file.write("\n")

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
    os.system('git commit -m " autocommit @ ' + filename_time_stamp + '"')
    os.system("git push -u origin master")


if __name__ == '__main__':
    
    # All file operations happen in the csvs folder
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd, "csvs"))
    
    try:
        device_identifier = sys.argv[1]
        sleep_time = int(sys.argv[2])
    except IndexError:
        print("Woops! Usage: python jtrack.py [device identifier] [sleep time] [device alias]")

    try:
        device_alias = sys.argv[3]
    except IndexError:
        print("No device alias given, CSV output will use the device identifier", device_identifier, "instead")
        device_alias = device_identifier
        
    try:
        track_device(device_identifier, device_alias)
    except Exception as e:
        print("Woops! Usage: python jtrack.py [device identifier] [sleep time] [device alias]")
        print(e)
        raise e


# android-9b72272b83db0551 = C
# android-fc090a3a8a86db64 = M
# android-a7226cbab44b68c5 = J
