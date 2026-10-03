"""
data_cleaning.py
================
Comprehensive data cleaning script for sample_data.csv:
1. Loads and inspects raw dataset
2. Identifies and removes duplicate rows
3. Corrects data types (Salary, Age, Dates, Booleans, Categoricals)
4. Detects and handles outliers / domain anomalies
5. Handles missing values (imputation)
6. Validates and saves cleaned dataset to cleaned_data.csv
"""

import os
import pandas as pd
import numpy as np

def print_separator(title=""):
    print("\n" + "=" * 65)
    if title:
        print(f" {title.upper()} ".center(65, "="))
        print("=" * 65)

def clean_data(input_file="sample_data.csv", output_file="cleaned_data.csv"):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    print_separator("Step 1: Loading Raw Data & Initial Inspection")
    # Read raw CSV with common null representations
    na_values = ["", " ", "NA", "N/A", "null", "None", "?", "Unknown", "invalid_date"]
    df = pd.read_csv(input_file, na_values=na_values, keep_default_na=True)
    
    print(f"Initial shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print("\nInitial Data Types & Non-Null Counts:")
    print(df.info())
    print("\nMissing Values per Column:")
    print(df.isnull().sum())

    # ---------------------------------------------------------
    # Step 2: Removing Duplicates
    # ---------------------------------------------------------
    print_separator("Step 2: Removing Duplicate Rows")
    initial_rows = len(df)
    duplicates_count = df.duplicated().sum()
    print(f"Exact duplicate rows detected: {duplicates_count}")
    
    if duplicates_count > 0:
        duplicate_rows = df[df.duplicated(keep=False)]
        print("Duplicated employee IDs:", duplicate_rows["employee_id"].unique().tolist())
        df = df.drop_duplicates().reset_index(drop=True)
        print(f"Removed {initial_rows - len(df)} duplicate rows. New row count: {len(df)}")
    else:
        print("No duplicate rows found.")

    # ---------------------------------------------------------
    # Step 3: Standardizing Categoricals & Correcting Data Types
    # ---------------------------------------------------------
    print_separator("Step 3: Correcting Data Types & Text Standardization")

    # 3.1 Clean text in string columns (trim leading/trailing spaces)
    str_cols = df.select_dtypes(include=object).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip().replace("nan", np.nan)

    # 3.2 Age: Map word representation ("thirty") to numeric and coerce to float
    word_to_num = {"thirty": 30, "twenty": 20, "forty": 40, "fifty": 50}
    df["age"] = df["age"].replace(word_to_num)
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    print("[x] 'age' converted to numeric")

    # 3.3 Salary: remove '$', ',', handle negatives and convert to numeric
    if "salary" in df.columns:
        df["salary"] = (
            df["salary"]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df["salary"] = pd.to_numeric(df["salary"], errors="coerce")
        print("[x] 'salary' cleaned of currency symbols/commas and converted to numeric float")

    # 3.4 Join Date: Mixed date formats & errors coerced to NaT
    if "join_date" in df.columns:
        df["join_date"] = pd.to_datetime(df["join_date"], format="mixed", errors="coerce")
        print("[x] 'join_date' parsed into datetime format")

    # 3.5 Gender standardization (e.g. 'M' -> 'Male', 'F'/'female' -> 'Female')
    if "gender" in df.columns:
        gender_map = {
            "M": "Male",
            "Male": "Male",
            "F": "Female",
            "female": "Female",
            "Female": "Female"
        }
        df["gender"] = df["gender"].map(gender_map)
        print("[x] 'gender' standardized to 'Male' and 'Female'")

    # 3.6 Department typos and abbreviations standardization
    if "department" in df.columns:
        dept_map = {
            "HR": "Human Resources",
            "Humman Resources": "Human Resources",
            "Human Resources": "Human Resources",
            "Engineering": "Engineering",
            "Marketing": "Marketing",
            "Finance": "Finance",
            "IT": "IT",
            "Sales": "Sales"
        }
        df["department"] = df["department"].replace(dept_map)
        print("[x] 'department' typos ('Humman Resources', 'HR') standardized")

    # 3.7 Remote Worker: Standardize booleans (True, False, 1, 0, Yes, No)
    if "remote_worker" in df.columns:
        bool_map = {
            "True": True, "TRUE": True, "true": True, "1": True, 1: True, "Yes": True, "yes": True,
            "False": False, "FALSE": False, "false": False, "0": False, 0: False, "No": False, "no": False
        }
        df["remote_worker"] = df["remote_worker"].map(bool_map)
        print("[x] 'remote_worker' standardized to boolean values")

    # ---------------------------------------------------------
    # Step 4: Detecting & Handling Outliers / Anomalies
    # ---------------------------------------------------------
    print_separator("Step 4: Handling Outliers & Logical Anomalies")

    # 4.1 Age anomalies: sensible working age is [18, 70]
    invalid_age_mask = (df["age"] < 18) | (df["age"] > 70)
    anomalous_ages = df.loc[invalid_age_mask, "age"].dropna().tolist()
    if anomalous_ages:
        print(f"[!] Anomalous 'age' values identified: {anomalous_ages}")
        df.loc[invalid_age_mask, "age"] = np.nan
        print("    -> Replaced invalid age values with NaN (to be imputed with median).")

    # 4.2 Salary anomalies: negative salary or extreme CEO/multimillion outlier
    # Reasonable threshold: salary > 0 and salary <= 1,000,000 (typical range: $40k - $200k)
    invalid_salary_mask = (df["salary"] <= 0) | (df["salary"] > 1_000_000)
    anomalous_salaries = df.loc[invalid_salary_mask, "salary"].dropna().tolist()
    if anomalous_salaries:
        print(f"[!] Anomalous 'salary' values identified: {anomalous_salaries}")
        # For negative salary, can check if it was just sign error or replace with NaN
        df.loc[invalid_salary_mask, "salary"] = np.nan
        print("    -> Replaced invalid salaries with NaN for median imputation.")

    # 4.3 Years of Experience anomalies:
    # Must be non-negative and experience cannot exceed (age - 18)
    invalid_exp_mask = (df["years_of_experience"] < 0) | (
        (df["age"].notnull()) & (df["years_of_experience"] > (df["age"] - 16))
    )
    anomalous_exp = df.loc[invalid_exp_mask, "years_of_experience"].dropna().tolist()
    if anomalous_exp:
        print(f"[!] Anomalous 'years_of_experience' values identified: {anomalous_exp}")
        df.loc[invalid_exp_mask, "years_of_experience"] = np.nan
        print("    -> Replaced anomalous experience values with NaN for imputation.")

    # 4.4 Performance score anomalies: Valid score is [0, 100]
    invalid_score_mask = (df["performance_score"] < 0) | (df["performance_score"] > 100)
    anomalous_scores = df.loc[invalid_score_mask, "performance_score"].dropna().tolist()
    if anomalous_scores:
        print(f"[!] Anomalous 'performance_score' values identified: {anomalous_scores}")
        df.loc[invalid_score_mask, "performance_score"] = np.nan
        print("    -> Replaced anomalous performance scores with NaN for imputation.")

    # ---------------------------------------------------------
    # Step 5: Handling Missing Values (Imputation)
    # ---------------------------------------------------------
    print_separator("Step 5: Handling Missing Values (Imputation)")

    # 5.1 Numeric Imputation with Median
    median_age = round(df["age"].median())
    df["age"] = df["age"].fillna(median_age).astype(int)
    print(f"[x] 'age' missing values imputed with median: {median_age}")

    # Impute salary by department median (or overall median if department median is NaN)
    dept_salary_medians = df.groupby("department")["salary"].transform("median")
    overall_salary_median = df["salary"].median()
    df["salary"] = df["salary"].fillna(dept_salary_medians).fillna(overall_salary_median).round(2)
    print(f"[x] 'salary' missing values imputed using department-specific median (overall median: ${overall_salary_median:,.2f})")

    median_exp = round(df["years_of_experience"].median())
    df["years_of_experience"] = df["years_of_experience"].fillna(median_exp).astype(int)
    print(f"[x] 'years_of_experience' missing values imputed with median: {median_exp}")

    median_score = round(df["performance_score"].median())
    df["performance_score"] = df["performance_score"].fillna(median_score).astype(int)
    print(f"[x] 'performance_score' missing values imputed with median: {median_score}")

    # 5.2 Categorical Imputation with Mode
    mode_gender = df["gender"].mode()[0]
    df["gender"] = df["gender"].fillna(mode_gender)
    print(f"[x] 'gender' missing values imputed with mode: '{mode_gender}'")

    mode_remote = df["remote_worker"].mode()[0]
    df["remote_worker"] = df["remote_worker"].fillna(mode_remote).astype(bool)
    print(f"[x] 'remote_worker' missing values imputed with mode: {mode_remote}")

    # 5.3 Date Imputation: forward-fill or median date
    if df["join_date"].isnull().sum() > 0:
        median_date = df["join_date"].dropna().quantile(0.5, interpolation="midpoint")
        df["join_date"] = df["join_date"].fillna(median_date)
        print(f"[x] 'join_date' missing values imputed with median date: {median_date.strftime('%Y-%m-%d')}")

    # ---------------------------------------------------------
    # Step 6: Final Verification & Export
    # ---------------------------------------------------------
    print_separator("Step 6: Final Verification & Export")
    print(f"Cleaned shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print("\nMissing values after cleaning:")
    print(df.isnull().sum())

    print("\nData Types:")
    print(df.dtypes)

    print("\nCleaned Data Sample (First 5 rows):")
    print(df.head())

    # Format join_date back to standard YYYY-MM-DD string for CSV output
    df["join_date"] = df["join_date"].dt.strftime("%Y-%m-%d")

    df.to_csv(output_file, index=False)
    print(f"\n[SUCCESS] Cleaned dataset successfully saved to: '{output_file}'")
    print_separator()

if __name__ == "__main__":
    clean_data()
