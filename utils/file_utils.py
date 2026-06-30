import os
import pandas as pd

def read_file(file_name):
    os.chdir("..")
    cwd = os.getcwd()
    input_path = cwd + "/data/" + file_name
    os.chdir("utils")
    df = pd.read_excel(input_path)
    return df

def write_file(df, file_name):
    os.chdir("..")
    cwd = os.getcwd()
    output_path = cwd + "/data/" + file_name
    os.chdir("utils")
    df.to_excel(output_path, index=False)