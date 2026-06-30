from datetime import datetime

def get_possible_years(first_year):
    curr_year = datetime.now().year
    # create list of all model years starting from first year to curr year
    model_years = [year for year in range(first_year, curr_year + 1)]
    return model_years
