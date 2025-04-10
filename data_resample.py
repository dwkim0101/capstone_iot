print("Starting python script...")
import tkinter as tk
from tkinter import filedialog
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import matplotlib
import json
import csv
import datetime
matplotlib.use('TkAgg')  # or 'Qt5Agg'
# must install openpyxl

# Create a root window and hide it
root = tk.Tk()
root.withdraw()

def on_close():
    """Function to handle when the window is closed"""
    root.quit()
    root.destroy()

# Get the current directory
current_dir = os.getcwd()

# Open a file dialog with the current directory as the default folder
file_paths = filedialog.askopenfilenames(
    title="Select Files",
    initialdir=current_dir  # Set the initial directory to the current directory
)

# Print the selected file paths
if file_paths:
    print("Selected files:")
    for file_path in file_paths:
        print(file_path)
else:
    print("No files selected")
    exit()

# Load the data from the selected files (csv and xlsx)
_dfs = []
for file_path in file_paths:
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        print(f"Unsupported file format: {file_path}")
        continue  # Skip unsupported files
    _dfs.append(df)

# Combine all loaded DataFrames into one
if _dfs:
    df = pd.concat(_dfs, ignore_index=True)
    print("Combined DataFrame:")
    print(df.head())
else:
    print("No valid files loaded.")
    exit(1)
print(df.dtypes)

""" DECIDE INDEX """
# Create a new function to create a listbox for column selection
def select_index_column(columns):
    def on_select():
        selection = listbox.curselection()
        if selection:
            selected_column.set(columns[selection[0]])
            listbox_window.destroy()

    # Create a new window for the listbox
    listbox_window = tk.Toplevel(root)
    listbox_window.title("Select Time Index Column")

    # Create a StringVar to store the selected column
    selected_column = tk.StringVar()

    # Create a Listbox and populate it with the column names
    listbox = tk.Listbox(listbox_window, selectmode=tk.SINGLE, height=len(columns), width=50)
    for column in columns:
        listbox.insert(tk.END, column)
    listbox.pack()

    # Create a button to confirm the selection
    select_button = tk.Button(listbox_window, text="Select", command=on_select)
    select_button.pack()

    # Wait for the window to close (i.e., user selection)
    listbox_window.wait_window()

    return selected_column.get()

# Get the column names and ask the user to select one from the listbox
selected_column = select_index_column(df.columns)

# If the user selected a valid column, set it as the index
if selected_column in df.columns:
    df.set_index(selected_column, inplace=True)
    print(f"DataFrame index set to: {selected_column}")
else:
    print("No valid column selected")
    exit()

""" CONVERT INDEX """
ind_type = type(df.index[0])
print(f"Index type: {ind_type}")
if ind_type == str:
    df.index = pd.to_datetime(df.index, format="mixed")
elif ind_type in [np.int64, int]:
    df.index = pd.to_datetime(df.index, unit='s')

""" SELECT DUET SERIAL COLUMN """
def select_duet_serial_column(columns):
    def on_select():
        selection = listbox.curselection()
        if selection:
            selected_column.set(columns[selection[0]])
            listbox_window.destroy()

    # Create a new window for the listbox
    listbox_window = tk.Toplevel(root)
    listbox_window.title("Select Duet Serial Number Column")

    # Create a StringVar to store the selected column
    selected_column = tk.StringVar()

    # Create a Listbox and populate it with the column names
    listbox = tk.Listbox(listbox_window, selectmode=tk.SINGLE, height=len(columns), width=50)
    for column in columns:
        listbox.insert(tk.END, column)
    listbox.pack()

    # Create a button to confirm the selection
    select_button = tk.Button(listbox_window, text="Select", command=on_select)
    select_button.pack()

    # Wait for the window to close (i.e., user selection)
    listbox_window.wait_window()

    return selected_column.get()

serial_number_column = select_duet_serial_column(df.columns)

""" GET RESAMPLE STUFF """
import re
period_re = re.compile("(\\d+)\\s*([a-zA-Z]+)\\s*$")

# Create a new function to select resample period and method
def select_resample_options():
    def on_confirm():
        period = period_entry.get()
        method = method_var.get()

        matches = period_re.findall(period)
        if matches:
            if matches[0][0].isdigit() and matches[0][1].lower() in ['s', 'min', 'h']:
                selected_period.set(matches[0][0] + matches[0][1].lower())
                selected_method.set(method)
                resample_window.destroy()
        else:
            error_label.config(text="Invalid period. Format: positive integer + 's', 'min', 'h'.")

    # Create a new window for resampling options
    resample_window = tk.Toplevel(root)
    resample_window.title("Resample Options")

    selected_period = tk.StringVar()
    selected_method = tk.StringVar()

    # Period entry
    period_label = tk.Label(resample_window, text="Resample Period (e.g., 5s, 2min, 1h):")
    period_label.pack()
    period_entry = tk.Entry(resample_window)
    period_entry.pack()

    # Error message for invalid input
    error_label = tk.Label(resample_window, text="", fg="red")
    error_label.pack()

    # Method dropdown (mean, median)
    method_var = tk.StringVar(resample_window)
    method_var.set("mean")  # default value
    method_label = tk.Label(resample_window, text="Resample Method:")
    method_label.pack()

    method_menu = tk.OptionMenu(resample_window, method_var, "mean", "median")
    method_menu.pack()

    # Confirm button
    confirm_button = tk.Button(resample_window, text="Confirm", command=on_confirm)
    confirm_button.pack()

    # Wait for the window to close (i.e., user input)
    resample_window.wait_window()

    return selected_period.get(), selected_method.get()

# Ask the user for the resample period and method
resample_period, resample_method = select_resample_options()

dfs = []
for sn, ddf in df.groupby(serial_number_column):
    ddf = ddf.drop(columns=[col_name for col_name, dt in ddf.dtypes.to_dict().items() if dt in [np.dtypes.ObjectDType]])
    if resample_method == "mean":
        resampled_df = ddf.resample(resample_period).mean()
    elif resample_method == "median":
        resampled_df = ddf.resample(resample_period).median()
    dfs.append((sn, resampled_df))

""" PLOT OPTIONS """

def select_serial_number(serial_numbers, title):
    def on_select():
        selection = listbox.curselection()
        if selection:
            selected_serial.set(serial_numbers[selection[0]])
            serial_window.destroy()

    serial_window = tk.Toplevel(root)
    serial_window.title(title)

    selected_serial = tk.StringVar()

    # Create a Listbox to display serial numbers
    listbox = tk.Listbox(serial_window, selectmode=tk.SINGLE, height=len(serial_numbers), width=50)
    for serial in serial_numbers:
        listbox.insert(tk.END, serial)
    listbox.pack()

    # Add a button to confirm selection
    select_button = tk.Button(serial_window, text="Select", command=on_select)
    select_button.pack()

    # Wait for user to select
    serial_window.wait_window()

    return selected_serial.get()

def select_data_column(columns, title="Select Data Column"):
    def on_select():
        selection = listbox.curselection()
        if selection:
            selected_column.set(columns[selection[0]])
            column_window.destroy()

    column_window = tk.Toplevel(root)
    column_window.title(title)

    selected_column = tk.StringVar()

    listbox = tk.Listbox(column_window, selectmode=tk.SINGLE, height=len(columns), width=50)
    for column in columns:
        listbox.insert(tk.END, column)
    listbox.pack()

    select_button = tk.Button(column_window, text="Select", command=on_select)
    select_button.pack()

    column_window.wait_window()

    return selected_column.get()

def plot_time_series():
    """Plot the time series for each Duet serial number"""
    selected_column = select_data_column(df.columns, title="Select Column for Time Series")
    plt.figure(figsize=(11, 7))
    for sn, ddf in dfs:
        plt.plot(ddf.index, ddf[selected_column], label=sn)  # Adjust to selected column
    plt.ylabel(f"{selected_column}")
    plt.legend()
    plt.show()

def compare_serial_numbers():
    """Plot comparison between two serial numbers"""
    serial_numbers = [sn for sn, _ in dfs]

    # Select X-axis serial number and data column
    x_serial = int(select_serial_number(serial_numbers, "Select Serial Number for X-axis"))
    x_column = select_data_column(df.columns, title=f"Select Column for {x_serial} (X-axis)")

    # Select Y-axis serial number and data column
    y_serial = int(select_serial_number(serial_numbers, "Select Serial Number for Y-axis"))
    y_column = select_data_column(df.columns, title=f"Select Column for {y_serial} (Y-axis)")

    # Find corresponding dataframes
    x_df = next(df for sn, df in dfs if sn == x_serial)
    y_df = next(df for sn, df in dfs if sn == y_serial)

    combined_df = x_df[[x_column]].join(y_df[[y_column]], how='inner', lsuffix='_x', rsuffix='_y')
    min_data = combined_df.min().min()
    max_data = combined_df.max().max()

    plt.figure(figsize=(11, 7))
    if x_column == y_column:
        sns.scatterplot(data=combined_df, x=f"{x_column}_x", y=f"{y_column}_y")
    else:
        sns.scatterplot(data=combined_df, x=f"{x_column}", y=f"{y_column}")

    if x_column == y_column:
        plt.plot([min_data, max_data], [min_data, max_data], color='black', linestyle='dotted', alpha=.7)

    plt.xlabel(f'{x_serial} {x_column}')
    plt.ylabel(f'{y_serial} {y_column}')
    plt.show()

# Create a new window with options: "Time Series" or "Compare"
def select_plot_option():
    plot_window = tk.Toplevel(root)
    plot_window.title("Select Plot Option")

    # Time Series Button
    time_series_button = tk.Button(plot_window, text="Time Series", command=plot_time_series)
    time_series_button.pack(pady=10)

    # Compare Button
    compare_button = tk.Button(plot_window, text="Compare", command=compare_serial_numbers)
    compare_button.pack(pady=10)

    plot_window.mainloop()

""" SELECT ACTION """

def save():
    # Ask for file location to save the resampled data
    save_path = filedialog.asksaveasfilename(
        title="Save Resampled Data", defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
    )
    if save_path:
        combined_df = pd.concat([df for sn, df in dfs])
        combined_df.to_csv(save_path)
        print(f"Resampled data saved to {save_path}")

def plot():
    select_plot_option()

# Create a new window with two buttons: "Plot Data" and "Save Resampled Data"
def select_action():
    action_window = tk.Toplevel(root)
    action_window.protocol("WM_DELETE_WINDOW", on_close)
    action_window.title("Select Action")

    plot_button = tk.Button(action_window, text="Plot Data", command=plot)
    plot_button.pack(pady=10)

    save_button = tk.Button(action_window, text="Save Resampled Data", command=save)
    save_button.pack(pady=10)

    action_window.mainloop()

# Display the action window with options to plot or save
select_action()

# 파일 경로 설정
serial_file = "serial_output.txt"
csv_file = "duet_data.csv"

# 시리얼 데이터 처리
json_lines = []
with open(serial_file, "r") as f:
    for line in f:
        if line.startswith("{") and (line.endswith("}\n") or line.endswith("}")):
            try:
                json_data = json.loads(line.strip())
                json_lines.append(json_data)
            except json.JSONDecodeError:
                print(f"JSON 파싱 오류: {line}")

# 데이터가 있는지 확인
if not json_lines:
    print("JSON 데이터를 찾을 수 없습니다.")
    exit(1)

# 먼저 첫 번째 JSON 객체의 키를 확인
print("첫 번째 JSON 객체 키:", json_lines[0].keys())

# CSV 데이터 준비
rows = []
for data in json_lines:
    # 기본 데이터 추가
    row = {}
    
    # JSON 데이터의 첫 번째 레벨 키를 모두 추가
    for key, value in data.items():
        if key != "pt1" and key != "pt2":
            row[key] = value
    
    # pt1 데이터 추가
    for key, value in data["pt1"].items():
        row[f"pt1_{key}"] = value
        
    # pt2 데이터 추가
    for key, value in data["pt2"].items():
        row[f"pt2_{key}"] = value
        
    rows.append(row)

# DataFrame으로 변환하여 처리
df = pd.DataFrame(rows)

# DataFrame 열 확인
print("DataFrame 열:", df.columns.tolist())

# 타임스탬프 생성
current_time = datetime.datetime.now()
if "sample_time" in df.columns:
    max_sample_time = df["sample_time"].max()
    start_time = current_time - datetime.timedelta(milliseconds=max_sample_time)
    
    # sample_time을 이용해 실제 타임스탬프 생성하고 새로운 timestamp 열 추가
    df["timestamp"] = df["sample_time"].apply(
        lambda x: (start_time + datetime.timedelta(milliseconds=x)).strftime("%Y-%m-%d %H:%M:%S")
    )
else:
    # sample_time이 없으면 현재 시간에서 약간의 시간차를 두고 생성
    df["timestamp"] = [
        (current_time - datetime.timedelta(seconds=len(df)-i)).strftime("%Y-%m-%d %H:%M:%S")
        for i in range(len(df))
    ]

# 타임스탬프를 맨 앞으로 정렬
cols = df.columns.tolist()
cols.remove("timestamp")
cols = ["timestamp"] + cols

df = df[cols]

# CSV 파일로 저장
df.to_csv(csv_file, index=False)
print(f"CSV 파일이 생성되었습니다: {csv_file}")
print(f"총 {len(df)}개의 데이터가 저장되었습니다.")

# 확인용으로 처음 몇 줄 출력
print("\n처음 5줄 데이터:")
print(df.head())