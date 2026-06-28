import re
import openpyxl
import os

MAKES = {
    "bmw": "BMW",
    "gmc": "GMC",
    "mini": "MINI",
    "vinfast": "VinFast"
}

MODEL_POWERTRAINS = {'electric', 'prime', 'plug-in', 'hybrid', 'ev', 'recharge'}

def normalize():
    os.chdir("..")
    cwd = os.getcwd()
    input_path = cwd + "/data/Uber_Cars.xlsx"
    wb = openpyxl.load_workbook(input_path, data_only=True)
    ws = wb.active
    #normalize_make(ws)
    normalize_model(ws)
    normalize_year(ws)
    wb.save(input_path)

def normalize_make(ws):
    header = [cell.value for cell in ws[1]]
    vehicle_col = header.index("Vehicle")
    make_col = vehicle_col + 3
    ws.cell(row=1, column=make_col).value = "Make"

    for row in range(2, ws.max_row + 1):
        vehicle = ws.cell(row=row, column=vehicle_col + 1).value
        if not vehicle:
            continue
        vehicle = vehicle.lower()
        vehicle_list = vehicle.split(" ")
        if "land rover" in vehicle:
            make = "Land Rover"
        else:
            make = vehicle_list[0]
        if make in MAKES:
            make = MAKES[make]
        else:
            make = make.title()
        ws.cell(row=row, column=make_col).value = make

def normalize_model(ws):
    header = [cell.value for cell in ws[1]]
    vehicle_col = header.index("Vehicle")
    make_col = header.index("Make")
    model_col = vehicle_col + 4
    ws.cell(row=1, column=model_col).value = "Model"

    for row in range(2, ws.max_row + 1):
        make = ws.cell(row=row, column=make_col + 1).value
        normalized_make = make.lower()
        vehicle = ws.cell(row=row, column=vehicle_col + 1).value
        if not vehicle:
            continue
        vehicle_normalized = vehicle.lower()
        #remove model from vehicle string
        start = vehicle_normalized.index(normalized_make)
        end = start + len(normalized_make)
        vehicle = vehicle[end:]
        #remove 4 digit year from vehicle string
        match = re.search(r'\d{4}', vehicle)
        if match:
            vehicle = vehicle[:match.start()].strip()
        vehicle = vehicle.lower()
        model_list = vehicle.split(" ")
        cleaned = [token.strip(",") for token in model_list]
        if "yes" in cleaned:
            yes_index = cleaned.index("yes")
            model_list = model_list[0:yes_index]
        last_part = model_list[-1]
        while last_part in MODEL_POWERTRAINS:
            model_list.pop()
            last_part = model_list[-1]
        model = [token.title() for token in model_list]
        model = " ".join(model)
        ws.cell(row=row, column=model_col).value = model

def normalize_year(ws):
    header = [cell.value for cell in ws[1]]
    vehicle_col = header.index("Vehicle")
    min_year_col = vehicle_col + 5
    ws.cell(row=1, column=min_year_col).value = "Minimum Year"

    for row in range(2, ws.max_row + 1):
        v = ws.cell(row=row, column=vehicle_col + 1).value
        if not v:
            continue
        match = re.search(r'\d{4}', v)
        if match:
            year_str = v[match.start():-1]
            min_year = year_str.split(" ")[0]
            print(min_year)
        ws.cell(row=row, column=min_year_col).value = min_year



def dedup_models():
    pass

normalize()