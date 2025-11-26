import re
from typing import Optional,Union
from pydantic import BaseModel, validator,Field,validator



'''-------------PYDANTIC CLASSES---------------'''
class signupmodel(BaseModel):
  username:str
  email:str
  password:str
  @validator('email')
  def emailchk(cls,v):
    if not re.match(r'.*@gmail\.com$',v):
      return StdRes(success=False,log='Invalid email address',data=None)
    else:
      return v

class StdRes(BaseModel):
  success:bool=Field(description="Determines successful and failed requests")
  log:Union[str,None]=Field(description="Describes the reason for a failed request")
  data:Union[str,None,dict,list,bool]

class otpsample(BaseModel):
  otp: str
  token:str

class LoginModel(BaseModel):
  username: str
  password : str

class logmodel(BaseModel):
  username:str
  logname:str

class logdataModel(BaseModel):
  temp:float
  hum:float
  