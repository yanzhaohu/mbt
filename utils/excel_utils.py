import pandas as pd

def read_excel(path):
    data = pd.read_excel(path)
    return data

def write_excel(path,data:pd):
        data.to_excel(path, index=False)
