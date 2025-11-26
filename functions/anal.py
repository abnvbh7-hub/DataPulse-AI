import pandas as pd
from functions.logger import get_data

def get_stats(id:int):
  x = get_data(id)
  df = pd.DataFrame(x,columns=['time','temp','hum'])
  df = df[['temp','hum']]
  payload = df.describe().to_dict()
  return payload

