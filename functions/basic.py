from fastapi import security
import jwt
import psycopg2
import bcrypt
from jwt import ExpiredSignatureError
from fastapi import FastAPI,Response,HTTPException,Request,Depends
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from schemas.all_schemas import signupmodel, StdRes, otpsample, LoginModel, logmodel, logdataModel

security = HTTPBearer()
secret = 'mywristbleedscrazy'

url = 'postgresql://postgres.qwehsvudkkvarrnjrzln:5ZEH-33tTwa3Ymb@aws-1-ap-south-1.pooler.supabase.com:5432/postgres'
conn = psycopg2.connect(url)
cursor = conn.cursor()

"""-----------------functions---------------"""

def get_all_mails()->list:
  mails = []
  cursor.execute(
      """select email from emaildb;"""
  )
  data = cursor.fetchall()
  for mail in data:
    mails.append(mail[0])
  return mails

def get_all_users()->list:
  data=[]
  cursor.execute(
    "select username from userdb;"
  )
  users = cursor.fetchall()
  for user in users:
    data.append(user[0])
  return data

def hashpw(pwd:str):
  return bcrypt.hashpw(pwd.encode('utf-8'),bcrypt.gensalt()).decode('utf-8')

def checkpw(password,hashedpw):
  return bcrypt.checkpw(password=password.encode('utf-8'),hashed_password=hashedpw.encode('utf-8'))

def get_user_info(username:str):
  cursor.execute(
      """select * from userdb
where username=(%s);""",(username,)
  )
  data = cursor.fetchall()
  return {
    'username':data[0][1],
    'password':data[0][2],
    'email':data[0][3]
}

def cookie_check(req:Request):
  if req.cookies.get('session-jwt'):
    session_token = req.cookies.get('session-jwt')
    payload = jwt.decode(session_token,secret,algorithms='HS256')
    username = payload.get('sub')
    users = get_all_users()
    if username not in users:
      return StdRes(success=False,log="No user found with the token!",data=None)
    else:
      return StdRes(success=True,log=f"{username} succesfully logged in!",data=username)
  else:
    return StdRes(success=False,log="No Token found, please login again!",data=None)

def header_check(sample:HTTPAuthorizationCredentials=Depends(security)):
  if sample.credentials:
    session_token = sample.credentials
    payload = jwt.decode(session_token,secret,algorithms='HS256')
    username = payload.get('sub')
    users = get_all_users()
    if username not in users:
      return StdRes(success=False,log="No user found with the token!",data=None)
    else:
      return StdRes(success=True,log=f"{username} succesfully logged in!",data=username)
  else:
    return StdRes(success=False,log="No Token found, please login again!",data=None)