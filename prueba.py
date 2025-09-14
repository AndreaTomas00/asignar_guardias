from datetime import datetime
print(datetime, type(datetime))
# Should show: <class 'datetime.datetime'> <class 'type'>
d = datetime(2024, 1, 1)
print(d.isoformat())