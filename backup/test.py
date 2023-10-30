from datetime import datetime, timedelta

dd = '2022-08-02 00:00:00'
print(type(dd))
str = datetime.strptime(dd, "%Y-%m-%d %H:%M:%S")
str = datetime.timestamp(str)
str = int(str) * 1000

str2 = datetime.strptime(dd, '%Y-%m-%d %H:%M:%S')
print(type(str2))
str2 = str2 - timedelta(hours=9)
str2 = datetime.timestamp(str2)
str2 = int(str2) * 1000
print(type(str))
print(str2)