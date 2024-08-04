from flask import Flask, request,jsonify, send_file

import pandas as pd 
import os 
import json
app=Flask(__name__)

upload_folder='uploads'
result_folder='result'

os.makedirs(upload_folder, exist_ok=True)
os.makedirs(result_folder,exist_ok=True)

@app.route('/configure_pipeline/',methods=['POST'])
def configure_pipeline():
    tasks=request.form.getlist('task')
    print(tasks)
    if not tasks:
        return jsonify({'error':"no task provided"}),400
    columns = request.form.getlist('columns')
    tolerable_missing_value = request.form.get('tolerable_missing_value')
    if tolerable_missing_value:
            tolerable_missing_value = json.loads(tolerable_missing_value)

    #     # Debugging: Print the retrieved tolerable missing values
    # print("Tolerable missing values:", tolerable_missing_value)
    files=request.form.getlist('file')
    # print(files)
    if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

    files = request.files['file']
    # print(files)
    if files.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if not files:
        return jsonify({'error':'no file provided'}),400
    filepath=os.path.join(upload_folder,files.filename)
    files.save(filepath)
    data=pd.read_excel(filepath)
    processed_data,report=run_pipeline(tasks,columns,tolerable_missing_value,data)
    result_filepath=os.path.join(result_folder,f'processed_{files.filename}')
    processed_data.to_excel(result_filepath,index=False)
    return jsonify({"processed_file":result_filepath,"report":report})
def run_pipeline(tasks,columns,tolerable_missing_value,data):
    processed_data = data.copy()
    report = {}
    for task in tasks:
        if task == "remove_duplicates":
            processed_data, dup_count = remove_duplicates(processed_data)
            report['duplicate_rows_removed'] = dup_count
        
        
        elif task == "check_column_duplicates":
            # Check for duplicates in specified columns
            if not columns:
                return processed_data, {"error": "No columns provided for duplicate check"}
            processed_data, dup_count = check_column_duplicates(processed_data, columns)
            report['duplicate_column_values'] = dup_count
        
        elif task == "check_missing_value":
            if not columns or not tolerable_missing_value:
                return processed_data,{"error":"No columns or tolerable value provided for missing value check"}
            missing_report=check_missing_value(processed_data,tolerable_missing_value,columns)
            report['missing_value']=missing_report
    
    report['row_count'] = len(processed_data)
    return processed_data, report
def check_missing_value(data,tolerable_missing_value,columns):
    missing_report={}
    row_count=len(data)
    for column in columns:
        print(column)
        if column in data.columns:
            # print(data[column])  
            missing_count=data[column].isnull().sum()
            # print(missing_count)

            missing_report[column]=int(missing_count)
            missing_percentage=(missing_count/row_count)*100
            if column in tolerable_missing_value:
                tolerance=tolerable_missing_value[column]
                
                if missing_percentage > tolerance:
                        missing_report[column] = f"Exceeds tolerance: {missing_percentage:.2f}% (Tolerance: {tolerance}%)"
                else:
                        missing_report[column] = f"Within tolerance: {missing_percentage:.2f}% (Tolerance: {tolerance}%)"
            else:
                    missing_report[column] = f"Missing values: {missing_percentage:.2f}% (No tolerance specified)"
        else:
            missing_report[column] = "Column not found in data"
    
    return missing_report


def remove_duplicates(data):
    initial_row_count = len(data)
    processed_data = data.drop_duplicates()
    duplicate_count = initial_row_count - len(processed_data)
    return processed_data, duplicate_count
def check_column_duplicates(data, columns):
    if not columns:
        return data, 0
    
    initial_row_count = len(data)
    
    if len(columns) == 1:
        # Check for duplicates in a single column
        processed_data = data[data.duplicated(subset=columns[0], keep=False)]
        duplicate_count = len(processed_data)
    else:
        # Check for duplicates in a combination of columns
        processed_data = data[data.duplicated(subset=columns, keep=False)]
        duplicate_count = len(processed_data)
    
    return processed_data, duplicate_count

if __name__ == '__main__':
    app.run(debug=True)