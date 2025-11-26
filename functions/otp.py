import numpy as np
import psycopg2
import sendgrid
from sendgrid.helpers.mail import Mail


url = 'postgresql://postgres.qwehsvudkkvarrnjrzln:5ZEH-33tTwa3Ymb@aws-1-ap-south-1.pooler.supabase.com:5432/postgres'
conn = psycopg2.connect(url)
cursor = conn.cursor()

sg = sendgrid.SendGridAPIClient(api_key="")

'''--------------FUNCTIONS--------------'''

def insert_user(username,password,email):
  cursor.execute(
        """insert into userdb(username,password,email,devices)
values (%s,%s,%s,get_devices(%s));""",(username,password,email,username)
    )
  conn.commit()

def verify_email(email:str):
  cursor.execute(
      """insert into emaildb(email,verified) values (%s,true);""",(email,)
  )
  conn.commit()

def send_mail(mail_id:str,otp:str):
  mail = Mail(
    from_email='marykumaribadugu@gmail.com',
    to_emails=mail_id,
    subject='OTP VERIFICATION',
    plain_text_content = otp
    )
  sg.send(mail)

def create_otp():
  otp = np.random.randint(100000,1000000,size=1)[0]
  return str(otp)

def log_otp(email,otp):
  cursor.execute(
      """ insert into otpdb(email,otp)
      values(%s,%s)""",(email,otp)
  )
  conn.commit()

def get_otp(user:str):
  cursor.execute(
      """select otp from otpdb where email=(%s) order by id desc limit 1;
      """,(user,)
  )
  data = cursor.fetchall()
  return data[0][0]

