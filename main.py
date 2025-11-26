import jwt
import pytz
import redis
import uvicorn
import numpy as np
import nest_asyncio
import pandas as pd
import plotly.express as px
from datetime import datetime,timedelta
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from fastapi import FastAPI,Response,HTTPException,Request,Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from schemas.all_schemas import signupmodel, StdRes, otpsample, LoginModel, logmodel, logdataModel
from functions.basic import get_all_mails, get_all_users, get_user_info, hashpw, checkpw, cookie_check, header_check, secret, security
from functions.otp import insert_user, log_otp, verify_email, send_mail, create_otp, get_otp
from functions.logger import get_loggers,get_stamp,get_logs,logger_status,delete_log, create_logid,create_log_ref,insert_data,create_log_table,get_logdata,get_data
from functions.anal import get_stats

nest_asyncio.apply()

ist = pytz.timezone('Asia/Kolkata')

r = redis.Redis(
    host='redis-14435.c264.ap-south-1-1.ec2.redns.redis-cloud.com',
    port=14435,
    decode_responses=True,
    username="default",
    password="1ItDoYRkO3FzrDSRbjj4FiGYWclrveeU",
)

app = FastAPI()

origins = ['https://b9318c49-2f9d-4663-b8c7-844ae0400201-00-1ruf1o27fgifn.pike.replit.dev',]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers= ["*"],
)


'''--------------ENDPOINTS--------------'''

@app.get('/')
def api_test():
  return{"API IS ONLINE!!!"}

@app.post('/register')
def register(sample:signupmodel,res:Response):
  username = sample.username
  email = sample.email
  password = sample.password
  users = get_all_users()
  if username in users:
    return StdRes(success=False,log='Choose another username!',data=None)
  else:
    otp = create_otp()
    print(otp)
    log_otp(email,otp)
    send_mail(email,otp)
    payload = {
    'sub':email,
    'exp':datetime.now()+timedelta(minutes=5)}
    token = jwt.encode(payload,secret,algorithm='HS256')
    data = {
        'username':username,
        'password':hashpw(password),
        'email':email
    }
    r.hset(f'user:{token}',mapping=data)
    r.expire(token,180)
    return StdRes(success=True,log=f"OTP sent to \t'{email}'\t",data=token)

@app.post('/verify')
def verify(sample:otpsample):
  otp = sample.otp
  session_token = sample.token
  if session_token:
    holder = jwt.decode(session_token,secret,algorithms='HS256')
    email = holder.get('sub')
    holder_otp = get_otp(email)
    if otp == holder_otp:
      bank = r.hgetall(f'user:{session_token}')
      print('user data retrieved from redis!')
      mails = get_all_mails()
      if email not in mails:
        verify_email(email=email)
        insert_user(bank.get('username'),bank.get('password'),email)
        return StdRes(success=True,log=f'{bank.get("username")} succesfully registered!',data=None)

      else:
        insert_user(bank.get('username'),bank.get('password'),email)
        return StdRes(success=True,log=f'{bank.get("username")} succesfully registered!',data=None)
    else:
      return StdRes(success=False,log='Entered incorrect OTP',data=None)
  else:
    return StdRes(success=False,log='Something went wrong, please register again!',data=None)

@app.post('/login')
def login(sample:LoginModel,res:Response):
  username = sample.username
  entered_password = sample.password
  users = get_all_users()
  if username not in users:
    return StdRes(success=False,log="Please register first!",data=None)
  else:
    info = get_user_info(username)
    if checkpw(entered_password,info.get('password')):
      payload = {
          'sub':username,
          'exp':datetime.now() + timedelta(days=7)
      }
      token = jwt.encode(payload,secret,algorithm='HS256')
      res.set_cookie(
          key='session-jwt',
          value=token,
          path='/'
      )
      return StdRes(success=True,log=f"{username} successfully logged in!",data=None)
    else:
      return StdRes(success=False,log="Incorrect Password",data=None)

@app.get('/logout')
def logout(res : Response,sample:StdRes = Depends(cookie_check)):
  if sample:
    if sample.success:
      res.delete_cookie(key='session-jwt')
      return StdRes(success =True,log="Logout success",data=None)
    else:
      return StdRes(success =False,log="Please login first!",data=None)
  else:
    return StdRes(success =False,log="Please login first!",data=None)

@app.get('/info/')
def get_home_info(id:int,sample:StdRes=Depends(cookie_check)):
  status = sample.success
  log = sample.log
  data = sample.data
  if id ==0:
    if status == True:
      return StdRes(success =True,log="Username extarcted",data=data)
    else:
      return StdRes(success=False,log="Unable to ACCESS",data=None)
  elif id ==1:
    if status == True:
      payload ={}
      payload['entries'] = get_loggers(data)
      payload['logger'] = logger_status(data)
      print(payload)
      return StdRes(success=True,log="Payload success",data=payload)
    else:
      return StdRes(success=False,log='Unable to ACCESS',data=None)
  elif id ==2:
    if status == True:
      stamps = []
      payload = []
      logs = get_logs(data)
      for log in logs:
        stamp = get_stamp(log)
        stamps.append(stamp)
      logid = logs[np.argmax(stamps)]
      data = get_data(logid)
      for sample in data:
        payload.append({"timestamp":datetime.strftime(sample[0].astimezone(ist),'%Y-%m-%d %H:%M:%S'),"temp":sample[1],"hum":sample[2]})
      return StdRes(success=True,log='Data sent!',data=payload)

@app.get('/logger/')
def logger_main(code:str,sample:StdRes=Depends(cookie_check),logid:Optional[int] = None):
  status = sample.success
  username = sample.data
  log = sample.log
  if not status:
    return StdRes(success=False,log='Please login again!',data=None)
  if status == True and code == 'get_logs':
    return StdRes(success=True,log="Successfully extraced logs!",data=get_logs(username))
  if status == True and code == 'del_log' and logid != None:
    logs = get_logs(username)
    if logid not in logs:
      return StdRes(success=False,log='Invalid Log id',data=None)
    else:
      delete_log(logid=logid,username=username)
      return StdRes(success=True,log=f"Log {logid}  deleted!",data=None)


@app.post('/create')
def create_logger(sample:logmodel,res:StdRes=Depends(cookie_check)):
  status = res.success
  log = res.log
  user= res.data
  username = sample.username
  logname = sample.logname
  if not status == True:
    return StdRes(success=False,log='Please login again!',data=None)
  if not username == user:
    return StdRes(success=False,log='Please login again!',data=None)
  logid = create_logid()
  create_log_ref(logid,logname,username)
  create_log_table(logid,logname,username)
  payload = {
      'username':username,
      'logid':logid,
      'logname':logname
  }
  r.set(str(logid),'off')
  token = jwt.encode(payload,secret,algorithm='HS256')
  return StdRes(success=True,log='Log created',data=token)

@app.post('/insertlog')
def log_data(logsample:logdataModel,sample:HTTPAuthorizationCredentials=Depends(security),res:StdRes=Depends(cookie_check)):
  status = res.success
  log = res.log
  user = res.data
  if not status == True:
    return StdRes(success=False,log='Please login again!',data=None)
  if not sample.credentials:
    return StdRes(success=False,log='Incorrect api token',data=None)
  else:
    token = sample.credentials
    payload = jwt.decode(token,secret,algorithms=['HS256'])
    temp = logsample.temp
    hum = logsample.hum
    username = payload.get('username')
    logname = payload.get('logname')
    logid = payload.get('logid')
    if not username == user:
      return StdRes(success=False,log='Please login again!',data=None)
    if r.get(str(logid)) == 'on':
      insert_data(logid,logname,username,temp,hum)
      return StdRes(success=True,log="Data logged",data={'logname':logname})
    elif r.get(str(logid)) == 'off':
      return StdRes(success=False,log='Flag closed! Oops!',data=None)

@app.get('/log_data/')
def get_log(id:int, res:StdRes=Depends(cookie_check)):
  status = res.success
  log=res.log
  user = res.data
  if status != True:
    return StdRes(success=False,log='Invalid token',data=None)
  else:
    if id is not None:
      logs = get_logs(user)
      if id not in logs:
        return StdRes(success=False,log="Not Authorized",data=None)
      else:
        payload = []
        data = get_data(id)
        for sample in data:
          payload.append({"timestamp":datetime.strftime(sample[0].astimezone(ist),'%Y-%m-%d %H:%M:%S'),"temp":sample[1],"hum":sample[2]})
        return StdRes(success=True,log='Data sent!',data=payload)

@app.post('/set_logflag/')
def set_flag(id:int,logid:int,res:StdRes=Depends(cookie_check)):
  status = res.success
  user=res.data
  logdata = res.log
  if not status == True:
    return StdRes(success=False,log='Please login again!',data=None)
  logs = get_logs(user)
  print(logs)
  if logid not in logs:
    return StdRes(success=False,log="Not Authorized",data=None)
  else:
    if id == 0:
      r.set(str(logid),'off')
      return  StdRes(success=True,log="Flag close",data=False)
    elif id ==1:
      r.set(str(logid),'on')
      return StdRes(success=True,log="Flag open",data=True)



uvicorn.run(app,host='0.0.0.0',port=8000)