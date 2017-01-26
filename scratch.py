import datetime
from time import sleep

time1 = datetime.datetime.now()
sleep(1)
time2 = datetime.datetime.now()

time_delta = (time2 - time1).total_seconds()
home_time = str(datetime.timedelta(seconds=int(time_delta)))

print(home_time)