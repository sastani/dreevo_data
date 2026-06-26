import io
import requests
import os
import pandas as pd
from datetime import datetime

def build_catalog():
    os.chdir("..")
    cwd = os.getcwd()
    input_path = cwd + "/data/Uber_Cars.xlsx"
    df = pd.read_excel(input_path)
    df = df[['Make']].drop_duplicates()
    make_model_list = []
    curr_year = datetime.now().year
    #first year in NHTSA dataset
    first_year = 1980
    #create list of all model years starting from first year in dataset to curr year
    model_years = [year for year in range(first_year, curr_year+1)]
    for row in df.itertuples():
        for model_year in model_years:
            url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/{row.Make}/modelyear/{model_year}?format=csv"
            r = requests.get(url)
            models_df = pd.read_csv(io.StringIO(r.text))
            if 'make_name' not in models_df.columns:
                continue
            models_df = models_df[['make_name', 'model_name']]
            for _, r in models_df.iterrows():
                make_model_year_dict = {"make": r['make_name'], "model": r['model_name'], "year": model_year}
                make_model_list.append(make_model_year_dict)
    make_model_year_df = pd.DataFrame(make_model_list)
    make_model_year_df = (make_model_year_df.groupby(['make', 'model'])
                          .agg(first_year_produced=('year', 'min'),
                               last_year_produced=('year', 'max')).reset_index())
    make_model_year_df.to_excel(cwd + "/data/Model_Production_Years.xlsx")


build_catalog()