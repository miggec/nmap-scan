import os
import subprocess
import datetime
from time import sleep
import sys


def device_connected(device: str):
    ip_scan = str(subprocess.check_output("nmap -sn 192.168.0.0/24", shell=True))
    if ip_scan.__contains__(device):
        return True


def scan_home(device: str, stime=2):
    """
    Scans the network for a certain device
    Yields the connect and disconnect times at a time interval defined in seconds by stime
    Also yields the time last spent connected if the device has just disconnected

    :param device: device name to scan for
    :param stime: sleep time between scan attempts
    :return:
    """

    already_connected = False
    connect_time_str = None
    connect_time = None
    disconnect_time_str = None
    disconnect_time = None
    time_spent_connected = None

    while True:

        if device_connected(device): # ("android-a7226cbab44b68c5")

            if not already_connected:  # just reconnected
                connect_time = datetime.datetime.now()
                disconnect_time = None
                already_connected = True
                print("Connected at", connect_time)

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
                    disconnect_time = possible_disconnect_time
                    print("Left at", disconnect_time)

                    time_delta = (disconnect_time - connect_time).total_seconds()
                    time_spent_connected = str(datetime.timedelta(seconds=int(time_delta)))
                    print("Time spent connected:", time_spent_connected)

                    already_connected = False

            elif not already_connected:  # remains disconnected
                time_spent_connected = None

        try:
            connect_time_str = connect_time.isoformat(sep=" ", timespec='minutes')
        except AttributeError:
            pass
        try:
            disconnect_time_str = disconnect_time.isoformat(sep=" ", timespec='minutes')
        except AttributeError:
            pass

        time_stamp = datetime.datetime.now().isoformat(sep=" ", timespec='minutes')

        yield[time_stamp, already_connected, connect_time_str, disconnect_time_str, time_spent_connected]

        sleep(stime)


def track_device(device):

    device_names = {
        "android-fc090a3a8a86db64": "Miguel",
        "android-a7226cbab44b68c5": "J_Android",
        "Jesses-iPhone": "J_iPhone"
    }

    filename_time_stamp = datetime.datetime.now().strftime("_%a-%d-%b_%H-%M-%S")
    csv_file_name = device_names[device] + filename_time_stamp + ".csv"

    with open(csv_file_name, 'w', encoding='utf-8') as outfile:
        outfile.write("time_stamp, is_connected, connect_time, disconnect_time, time_spent_connected,\n")

    while True:
        for scan in scan_home('android-fc090a3a8a86db64'):
            with open(csv_file_name, 'a', encoding='utf-8') as append_file:
                    for column in scan:
                        append_file.write(str(column) + ",")
                    append_file.write("\n")

            commit_to_git(filename_time_stamp)


def commit_to_git(filename_time_stamp):
    """
    Should probably use the developer API for this!

    :param filename_time_stamp:
    :return:
    """
    os.system("git add .")
    commit_command = 'git commit -m " autocommit @ ' + filename_time_stamp + '"'
    os.system(commit_command)
    os.system("git push -u origin master")

known_devices = {
    "M": "android-fc090a3a8a86db64",
    "J_android": "android-a7226cbab44b68c5",
    "J_iPhone": "Jesses-iPhone",
}

track_device(known_devices[sys.argv[1]])

# android-9b72272b83db0551 = C
# android-fc090a3a8a86db64 = M
# android-a7226cbab44b68c5 = J
