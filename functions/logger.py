import psycopg2
import pytz
import numpy as np
from datetime import datetime,timedelta,timezone
from schemas.all_schemas import StdRes

url = 'postgresql://postgres.qwehsvudkkvarrnjrzln:5ZEH-33tTwa3Ymb@aws-1-ap-south-1.pooler.supabase.com:5432/postgres'
conn = psycopg2.connect(url)
cursor = conn.cursor()


ist = pytz.timezone('Asia/Kolkata')

'''--------------FUNCTIONS--------------'''

def get_loggers(name:str):
  cursor.execute(
      """select * from check_devices(%s)""",(name,)
  )
  data = cursor.fetchall()
  return data[0][0]


def get_stamp(id:int):
  cursor.execute(
      """select at from _%s order by at desc limit 1;""",(id,)
  )
  data = cursor.fetchall()
  try:
    return data[0][0]
  except (IndexError):
    return datetime(2025,1,1,1,1,1, tzinfo=timezone.utc)


def get_logs(name:str):
  logs=[]
  cursor.execute(
      """select logid from loggerdb where username =(%s)""",(name,)
  )
  data =cursor.fetchall()
  for log in data:
    logs.append(log[0])
  return logs

def logger_status(name:str):
  res = []
  logs = get_logs(name)
  for log in logs:
    stamp = get_stamp(log)
    if datetime.now(ist) - stamp.astimezone(ist) > timedelta(seconds=10):
      res.append(False)
    else:
      res.append(True)
  if True in res:
    return True
  else:
    return False
def get_data(id:int):
  cursor.execute(
      """select at,temp,hum from _%s;""",(id,)
  )
  data = cursor.fetchall()
  return data


def delete_log(logid:int,username:str):
  try:
    cursor.execute(
        """drop table _%s;
  update userdb
  set devices = check_devices(%s) - 1
  where username = %s;
  delete from loggerdb
  where logid = %s""",(logid,username,username,logid)
    )
    conn.commit()
    return "Deleted"
  except Exception as e:
    return e


def create_logid():
  id = np.random.randint(0,99999999)
  return id

def create_log_ref(logid,logname,username):
  cursor.execute(
      """insert into loggerdb(logid,logname,username,password)
values (%s,%s,%s,%s);
update userdb
set devices = get_devices(%s)
where username = %s;""",(logid,logname,username,username,username,username)
  )
  conn.commit()
  return "user_log_commited"
def create_log_table(logid,logname,username):
  cursor.execute(
      """create table _%s(
  logname text not null check(logname=%s),
  username text not null  check(username= %s),
  at timestamptz default now(),
  temp int not null,
  hum int not null,
  foreign key (username)
  references userdb(username)
  on delete cascade
);""",(logid,logname,username)
  )
  conn.commit()
  return"Log created"

def insert_data(logid,logname,username,temp,hum):
  cursor.execute("""
  insert into _%s(logname,username,temp,hum)
values(%s,%s,%s,%s)
""",(logid,logname,username,temp,hum))
  conn.commit()
  return "Data Logged"

def get_logdata(id:int):
  payload =[]
  cursor.execute("""
select at, temp, hum from _%s
""",(id,))
  data = cursor.fetchall()
  for sample in data:
    payload.append({"timestamp":datetime.strftime(sample[0].astimezone(ist),'%Y-%m-%d %H:%M:%S'),"temp":sample[1],"hum":sample[2]})
  return StdRes(success=True,log='Data sent!',data=payload)
