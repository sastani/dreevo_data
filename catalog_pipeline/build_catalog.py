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
    make_model_year_df.to_excel(cwd + "/data/Model_Production_Years.xlsx", index=False)

def match_and_filter_models():
    os.chdir("..")
    cwd = os.getcwd()
    uber_input_path = cwd + "/data/Uber_Cars.xlsx"
    uber_df = pd.read_excel(uber_input_path)
    #create copy of make and model columns
    uber_df[['make_copy', 'model_copy']] = uber_df[['Make', 'Model']]
    #convert column names to lowercase
    uber_df.columns = uber_df.columns.str.lower()
    #convert all makes and model to lowercase
    make_model_cols = ['make_copy', 'model_copy']
    uber_df[make_model_cols] = uber_df[make_model_cols].apply(lambda x: x.str.lower())
    nhtsa_input_path = cwd + "/data/Model_Production_Years.xlsx"
    nhtsa_df = pd.read_excel(nhtsa_input_path)
    # create copy of make and model columns
    nhtsa_df[['make_copy', 'model_copy']] = nhtsa_df[['make', 'model']]
    # convert all makes and model to lowercase
    nhtsa_df[make_model_cols] = nhtsa_df[make_model_cols].apply(lambda x: x.str.lower())
    #if model is a "class" or "series", apply special function to keep everything before it
    uber_df['model_copy'] = uber_df['model_copy'].str.split("-class").str[0]
    nhtsa_df['model_copy'] = nhtsa_df['model_copy'].str.split("-class").str[0]
    uber_df['model_copy'] = uber_df['model_copy'].str.split("-series").str[0]
    pd.set_option('display.max_columns', None)
    uber_df.loc[uber_df['model_copy'] == 'q4 e-tron', 'model_copy'] = uber_df['model_copy'].str.split(" ").str[0]
    # set all values for model_copy in uber df where make is 'polestar' to make and model concatenated
    uber_df.loc[uber_df['make_copy'] == 'polestar', 'model_copy'] = uber_df['make_copy'] + " " + uber_df['model_copy']
    #set all values for model_copy in uber df where make is 'bmw' to first character before "-series"
    uber_df.loc[uber_df['make_copy'] == 'bmw', 'model_copy'] = uber_df['model_copy'].str.split("-series").str[0]
    #set all values for model_copy in nhtsa df where make is 'bmw' and model starts with digit to first character
    bmw_digit_mask = (nhtsa_df['make_copy'] == 'bmw') & (nhtsa_df['model_copy'].str[0].str.isdigit())
    nhtsa_df.loc[bmw_digit_mask, 'model_copy'] = nhtsa_df['model_copy'].str[0]
    # set all values for model_copy in uber df where make is 'mercedes' to string before "-class"
    uber_df.loc[uber_df['make_copy'] == 'mercedes-benz', 'model_copy'] = uber_df['model_copy'].str.split("-class").str[0]
    # set all values for model_copy in nhtsa df where make is 'mercedes' to string before "-class"
    nhtsa_df.loc[nhtsa_df['make_copy'] == 'mercedes-benz', 'model_copy'] = nhtsa_df['model_copy'].str.split("-class").str[0]
    uber_df = uber_df[['make', 'make_copy', 'model_copy', 'minimum year', 'uber tier']]
    nhtsa_df = nhtsa_df[['model', 'make_copy', 'model_copy', 'first_year_produced', 'last_year_produced']]
    merged_df =uber_df.merge(nhtsa_df, how='inner', on=['make_copy', 'model_copy'])
    filtered_df = merged_df.loc[(merged_df['minimum year'] < merged_df['last_year_produced']) |
                                (merged_df['minimum year'] == merged_df['last_year_produced'])|
                                (merged_df['minimum year'] < merged_df['first_year_produced'])].copy()
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    filtered_df['model_family'] = None
    #create model family for all bmws starting with a digit
    bmw_digit_mask = (filtered_df['make_copy'] == 'bmw') & (filtered_df['model_copy'].str[0].str.isdigit())
    filtered_df.loc[bmw_digit_mask, 'model_family'] = filtered_df['model_copy'].str[0] + "-Series"
    #create model family for all mercedes
    filtered_df.loc[filtered_df['make_copy'] == 'mercedes-benz', 'model_family'] = filtered_df['model'].str.split(" ").str[0]
    mercedes_class_mask = (filtered_df['make_copy'] == 'mercedes-benz') & (filtered_df['model_family'].str.contains("EQ"))
    filtered_df.loc[mercedes_class_mask, 'model_family'] = filtered_df['model'].str.split("-").str[0]
    no_space_mask = mercedes_class_mask & filtered_df['model'].str.split(" ").str[1].isna()
    has_space_mask = mercedes_class_mask & filtered_df['model'].str.split(" ").str[1].notna()
    filtered_df.loc[no_space_mask, 'model'] = filtered_df['model'].str.split("-").str[0]
    filtered_df.loc[has_space_mask, 'model'] = filtered_df['model'].str.split("-").str[0] + " " + filtered_df['model'].str.split(" ").str[1]
    filtered_df = filtered_df[['make', 'model_family', 'model', 'minimum year', 'uber tier', 'first_year_produced', 'last_year_produced']]
    #drop duplicate rows for mercedes and bmw
    filtered_df = filtered_df.drop_duplicates()
    filtered_df.to_excel(cwd + "/data/Uber_Model_Production_Years.xlsx", index=False)


#build_catalog()
match_and_filter_models()
