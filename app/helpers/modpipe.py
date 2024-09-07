from json import dumps as dump_json_string

from flask import request
from app import logs
def get_form_data(fields:list, form_data={}):
    logs.info(request.form)
    for data in request.form:
        if data in fields:
            data_list = request.form.getlist(data)
            if len(data_list) > 1:
                logs.info(f"{data}({len(data_list)}): {data_list}")
                form_data[data] = dump_json_string(data_list)
            else:
                form_data[data] = data_list[0]
            logs.info(f"    {data}: {form_data[data]}")
        else:
            form_data[data] = None
    return form_data