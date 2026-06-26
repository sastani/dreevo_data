import re
import openpyxl
import os

MAKES = {
    "bmw": "BMW",
    "gmc": "GMC",
    "mini": "MINI",
    "vinfast": "VinFast"
}

def normalize():
    os.chdir("..")
    cwd = os.getcwd()
    input_path = cwd + "/data/raw/Uber_Cars.xlsx"
    wb = openpyxl.load_workbook(input_path, data_only=True)
    ws = wb.active
    normalize_make(ws)
    normalize_model(ws)
    wb.save(input_path)

def normalize_make(ws):
    header = [cell.value for cell in ws[1]]
    vehicle_col = header.index("Vehicle")
    make_col = vehicle_col + 3
    ws.cell(row=1, column=make_col).value = "Make"

    for row in range(2, ws.max_row + 1):
        v = ws.cell(row=row, column=vehicle_col + 1).value
        if not v:
            continue
        v = v.lower()
        vehicle_list = v.split(" ")
        if "land rover" in v:
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
    model_col = vehicle_col + 4
    ws.cell(row=1, column=model_col).value = "Model"

    for row in range(2, ws.max_row + 1):
        v = ws.cell(row=row, column=vehicle_col + 1).value
        if not v:
            continue
        match = re.search(r'\d{4}', v)
        if match:
            v = v[:match.start()].strip()
        v = v.lower()
        vehicle_list = v.split(" ")
        if "land rover" in v:
            if "range rover" in v:
                model = " ".join(vehicle_list[2:])
            else:
                model = vehicle_list[2]
            model = model.title()
        else:
            cleaned = [token.strip(",") for token in vehicle_list]
            if "yes" in cleaned:
                yes_index = cleaned.index("yes")
                model = vehicle_list[1:yes_index]
            else:
                model = vehicle_list[1:]
            model = [token.title() for token in model]
            model = " ".join(model)
        ws.cell(row=row, column=model_col).value = model


def dedup_models():
    pass

normalize()