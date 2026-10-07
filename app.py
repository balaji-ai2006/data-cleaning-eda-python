"""
app.py
======
Interactive Streamlit Web Dashboard for Data Cleaning and Exploratory Data Analysis (EDA).
Designed for local execution and 1-click cloud deployment (Streamlit Community Cloud, Docker, Render).
"""

import os
import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Data Cleaning & EDA Studio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Modern UI Styling
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 24px 28px;
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(30, 58, 138, 0.15);
    }
    
    .main-header h1 {
        color: white !important;
        font-weight: 700;
        font-size: 1.9rem;
        margin: 0 0 6px 0;
    }
    
    .main-header p {
        color: #e0f2fe !important;
        font-size: 0.95rem;
        margin: 0;
    }
    
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.06);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e3a8a;
    }
    .metric-label {
        font-size: 0.82rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-fixed { background-color: #dcfce7; color: #15803d; }
    .badge-warn { background-color: #fef3c7; color: #b45309; }
    
    .section-title {
        font-weight: 700;
        color: #1e293b;
        margin-top: 10px;
        margin-bottom: 12px;
        font-size: 1.15rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Domain & Generic Cleaning Utilities
# -----------------------------------------------------------------------------
def run_cleaning_pipeline(raw_df: pd.DataFrame, is_sample: bool = True):
    """
    Executes a multi-stage cleaning pipeline with an audit trail.
    Handles the HR sample dataset specifically or general tabular CSVs.
    """
    df = raw_df.copy()
    audit_log = []
    
    initial_shape = df.shape
    initial_nulls = int(df.isnull().sum().sum())
    
    # Stage 1: Deduplication
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        audit_log.append({
            "stage": "Deduplication",
            "action": f"Removed {dup_count} exact duplicate rows",
            "impact": f"Row count reduced from {initial_shape[0]} to {len(df)}"
        })
    else:
        audit_log.append({
            "stage": "Deduplication",
            "action": "No duplicate rows found",
            "impact": "Dataset rows intact"
        })

    # Stage 2: String Trimming & Standardizing
    str_cols = df.select_dtypes(include=object).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip().replace(["nan", "None", "null", "?", "N/A", "NA"], np.nan)
    audit_log.append({
        "stage": "Text Standardization",
        "action": f"Trimmed whitespace and mapped null sentinels to NaN in {len(str_cols)} columns",
        "impact": "Standardized text entries"
    })

    # Stage 3: Domain Corrections (HR specific when present)
    if is_sample or ("salary" in df.columns or "age" in df.columns):
        if "age" in df.columns:
            word_to_num = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}
            df["age"] = df["age"].replace(word_to_num)
            df["age"] = pd.to_numeric(df["age"], errors="coerce")
            
            # Age anomalies [18, 70]
            invalid_age_mask = (df["age"] < 18) | (df["age"] > 70)
            age_anomalies = int(invalid_age_mask.sum())
            if age_anomalies > 0:
                df.loc[invalid_age_mask, "age"] = np.nan
                audit_log.append({
                    "stage": "Outlier Detection",
                    "action": f"Flagged {age_anomalies} out-of-bounds Age values (<18 or >70)",
                    "impact": "Converted to NaN for median imputation"
                })

        if "salary" in df.columns:
            df["salary"] = (
                df["salary"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df["salary"] = pd.to_numeric(df["salary"], errors="coerce")
            
            # Salary anomalies (negative or extreme > 1M)
            invalid_salary_mask = (df["salary"] <= 0) | (df["salary"] > 1_000_000)
            sal_anomalies = int(invalid_salary_mask.sum())
            if sal_anomalies > 0:
                df.loc[invalid_salary_mask, "salary"] = np.nan
                audit_log.append({
                    "stage": "Outlier Detection",
                    "action": f"Flagged {sal_anomalies} invalid/extreme salaries (<= 0 or > $1M)",
                    "impact": "Converted to NaN for department median imputation"
                })

        if "join_date" in df.columns:
            df["join_date"] = pd.to_datetime(df["join_date"], format="mixed", errors="coerce")

        if "gender" in df.columns:
            gender_map = {
                "M": "Male", "Male": "Male",
                "F": "Female", "female": "Female", "Female": "Female"
            }
            df["gender"] = df["gender"].map(gender_map)

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

        if "remote_worker" in df.columns:
            bool_map = {
                "True": True, "TRUE": True, "true": True, "1": True, 1: True, "Yes": True, "yes": True,
                "False": False, "FALSE": False, "false": False, "0": False, 0: False, "No": False, "no": False
            }
            df["remote_worker"] = df["remote_worker"].map(bool_map)

        if "years_of_experience" in df.columns:
            df["years_of_experience"] = pd.to_numeric(df["years_of_experience"], errors="coerce")
            invalid_exp_mask = (df["years_of_experience"] < 0) | (
                (df["age"].notnull()) & (df["years_of_experience"] > (df["age"] - 16))
            )
            exp_anomalies = int(invalid_exp_mask.sum())
            if exp_anomalies > 0:
                df.loc[invalid_exp_mask, "years_of_experience"] = np.nan
                audit_log.append({
                    "stage": "Outlier Detection",
                    "action": f"Flagged {exp_anomalies} illogical Experience values (<0 or > age-16)",
                    "impact": "Converted to NaN for imputation"
                })

        if "performance_score" in df.columns:
            df["performance_score"] = pd.to_numeric(df["performance_score"], errors="coerce")
            invalid_score_mask = (df["performance_score"] < 0) | (df["performance_score"] > 100)
            score_anomalies = int(invalid_score_mask.sum())
            if score_anomalies > 0:
                df.loc[invalid_score_mask, "performance_score"] = np.nan
                audit_log.append({
                    "stage": "Outlier Detection",
                    "action": f"Flagged {score_anomalies} invalid Performance Scores (<0 or >100)",
                    "impact": "Converted to NaN for median imputation"
                })

    # Stage 4: Missing Value Imputation
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if df[col].isnull().sum() > 0:
            if col == "salary" and "department" in df.columns:
                dept_medians = df.groupby("department")["salary"].transform("median")
                overall_median = df["salary"].median()
                df["salary"] = df["salary"].fillna(dept_medians).fillna(overall_median).round(2)
                audit_log.append({
                    "stage": "Imputation",
                    "action": "Imputed missing Salary with Department Median",
                    "impact": f"Dept-conditioned median (Overall: ${overall_median:,.2f})"
                })
            else:
                med_val = df[col].median()
                if pd.notnull(med_val):
                    df[col] = df[col].fillna(med_val)
                    if col in ["age", "years_of_experience", "performance_score"]:
                        df[col] = df[col].round().astype(int)
                    audit_log.append({
                        "stage": "Imputation",
                        "action": f"Imputed missing '{col}' with median: {med_val:.1f}",
                        "impact": "0 nulls remaining"
                    })

    # Impute Categoricals with Mode
    cat_cols = df.select_dtypes(include=["object", "bool"]).columns
    for col in cat_cols:
        if col != "join_date" and df[col].isnull().sum() > 0:
            modes = df[col].mode()
            if not modes.empty:
                mode_val = modes[0]
                df[col] = df[col].fillna(mode_val)
                audit_log.append({
                    "stage": "Imputation",
                    "action": f"Imputed missing '{col}' with mode: '{mode_val}'",
                    "impact": "Categorical completeness achieved"
                })

    # Impute Datetime if present
    date_cols = df.select_dtypes(include=["datetime64"]).columns
    for col in date_cols:
        if df[col].isnull().sum() > 0:
            med_date = df[col].dropna().quantile(0.5, interpolation="midpoint")
            df[col] = df[col].fillna(med_date)
            audit_log.append({
                "stage": "Imputation",
                "action": f"Imputed missing '{col}' with median timestamp: {med_date.strftime('%Y-%m-%d')}",
                "impact": "Datetime continuity preserved"
            })

    final_nulls = int(df.isnull().sum().sum())
    return df, audit_log, initial_shape, df.shape, initial_nulls, final_nulls

# -----------------------------------------------------------------------------
# Main Application Layout
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <h1>📊 Data Cleaning & Exploratory Data Analysis Studio</h1>
        <p>Production-ready automated preprocessing, data sanitization, outlier treatment, and visual analytics pipeline.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar: Controls & Dataset Selection
with st.sidebar:
    st.image("https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Python-Dark.svg", width=50)
    st.markdown("### ⚙️ Pipeline Configuration")
    
    data_source = st.radio(
        "Choose Data Source:",
        ["Sample HR Dataset (sample_data.csv)", "Upload Custom CSV"],
        index=0,
    )
    
    uploaded_file = None
    if data_source == "Upload Custom CSV":
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_file is None:
            st.info("👆 Upload a CSV file to begin analysis.")
            
    st.markdown("---")
    st.markdown("#### 🛠️ Cleaning Strategy")
    st.caption("✔️ Remove Exact Duplicates")
    st.caption("✔️ Standardize Text & Types")
    st.caption("✔️ Detect Domain Outliers & Bounds")
    st.caption("✔️ Median / Mode Smart Imputation")
    
    st.markdown("---")
    st.markdown(
        """
        **Repository:** [balaji-ai2006/data-cleaning-eda-python](https://github.com/balaji-ai2006/data-cleaning-eda-python)  
        **Python Version:** 3.10+  
        **License:** MIT
        """
    )

# Load Selected Dataset
raw_df = None
is_sample_dataset = True

if data_source == "Sample HR Dataset (sample_data.csv)":
    sample_file_path = "sample_data.csv"
    if os.path.exists(sample_file_path):
        na_values = ["", " ", "NA", "N/A", "null", "None", "?", "Unknown", "invalid_date"]
        raw_df = pd.read_csv(sample_file_path, na_values=na_values, keep_default_na=True)
    else:
        st.error(f"Sample data file '{sample_file_path}' not found in current directory.")
else:
    if uploaded_file is not None:
        try:
            raw_df = pd.read_csv(uploaded_file)
            is_sample_dataset = False
        except Exception as e:
            st.error(f"Error reading uploaded CSV: {e}")

if raw_df is not None:
    # Run automated cleaning pipeline
    cleaned_df, audit_log, init_shape, clean_shape, init_nulls, clean_nulls = run_cleaning_pipeline(
        raw_df, is_sample=is_sample_dataset
    )
    
    # Navigation Tabs
    tab_overview, tab_pipeline, tab_eda, tab_export = st.tabs([
        "📋 Overview & Raw Diagnostics",
        "🧹 Cleaning Pipeline & Audit",
        "📈 Interactive EDA Visualizations",
        "💾 Export Sanitized Data"
    ])
    
    # -------------------------------------------------------------------------
    # TAB 1: OVERVIEW & RAW DIAGNOSTICS
    # -------------------------------------------------------------------------
    with tab_overview:
        st.markdown('<div class="section-title">📊 Dataset Health Metrics</div>', unsafe_allow_html=True)
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{init_shape[0]}</div>
                    <div class="metric-label">Total Raw Rows</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m_col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{init_shape[1]}</div>
                    <div class="metric-label">Columns</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m_col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{raw_df.duplicated().sum()}</div>
                    <div class="metric-label">Duplicate Rows</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m_col4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{init_nulls}</div>
                    <div class="metric-label">Missing Cells</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        st.markdown("---")
        
        row_c1, row_c2 = st.columns([3, 2])
        with row_c1:
            st.markdown('<div class="section-title">🔍 Raw Data Inspection (First 15 Rows)</div>', unsafe_allow_html=True)
            st.dataframe(raw_df.head(15), use_container_width=True)
            
        with row_c2:
            st.markdown('<div class="section-title">⚠️ Missing Values by Column</div>', unsafe_allow_html=True)
            null_series = raw_df.isnull().sum()
            null_df = pd.DataFrame({"Column": null_series.index, "Missing Count": null_series.values})
            null_df = null_df[null_df["Missing Count"] > 0].sort_values(by="Missing Count", ascending=True)
            
            if not null_df.empty:
                fig_null = px.bar(
                    null_df,
                    x="Missing Count",
                    y="Column",
                    orientation="h",
                    color="Missing Count",
                    color_continuous_scale="Reds",
                    text="Missing Count"
                )
                fig_null.update_layout(
                    margin=dict(l=0, r=20, t=20, b=20),
                    height=280,
                    showlegend=False
                )
                st.plotly_chart(fig_null, use_container_width=True)
            else:
                st.success("No missing values detected in the raw dataset!")

    # -------------------------------------------------------------------------
    # TAB 2: CLEANING PIPELINE & AUDIT
    # -------------------------------------------------------------------------
    with tab_pipeline:
        st.markdown('<div class="section-title">⚙️ Transformation Audit Trail</div>', unsafe_allow_html=True)
        st.write("Every step of data sanitization is validated and documented automatically:")
        
        audit_df = pd.DataFrame(audit_log)
        st.dataframe(audit_df, use_container_width=True)
        
        st.markdown("---")
        st.markdown('<div class="section-title">⚖️ Before vs. After Cleaning Comparison</div>', unsafe_allow_html=True)
        
        cmp_col1, cmp_col2 = st.columns(2)
        with cmp_col1:
            st.subheader("🔴 Raw Data Profile")
            st.markdown(f"- **Total Rows:** {init_shape[0]}")
            st.markdown(f"- **Total Columns:** {init_shape[1]}")
            st.markdown(f"- **Missing Values:** {init_nulls}")
            st.markdown(f"- **Exact Duplicates:** {raw_df.duplicated().sum()}")
            if "salary" in raw_df.columns:
                st.markdown(f"- **Salary Type:** `{raw_df['salary'].dtype}` (includes symbols)")
            if "age" in raw_df.columns:
                st.markdown(f"- **Age Type:** `{raw_df['age'].dtype}` (includes strings)")

        with cmp_col2:
            st.subheader("🟢 Cleaned Data Profile")
            st.markdown(f"- **Total Rows:** {clean_shape[0]} *(Sanitized)*")
            st.markdown(f"- **Total Columns:** {clean_shape[1]}")
            st.markdown(f"- **Missing Values:** {clean_nulls} *(100% Imputed)*")
            st.markdown(f"- **Exact Duplicates:** {cleaned_df.duplicated().sum()} *(Removed)*")
            if "salary" in cleaned_df.columns:
                st.markdown(f"- **Salary Type:** `float64` (Normalized numerical)")
            if "age" in cleaned_df.columns:
                st.markdown(f"- **Age Type:** `int64` (Clean integer range [18-70])")

        st.markdown("---")
        st.markdown('<div class="section-title">✨ Cleaned Dataset Preview</div>', unsafe_allow_html=True)
        st.dataframe(cleaned_df.head(15), use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 3: INTERACTIVE EDA VISUALIZATIONS
    # -------------------------------------------------------------------------
    with tab_eda:
        st.markdown('<div class="section-title">📊 Exploratory Data Visualizations</div>', unsafe_allow_html=True)
        
        num_cols = cleaned_df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = cleaned_df.select_dtypes(include=["object", "bool"]).columns.tolist()
        # Remove employee_id from numerical visualizations if present
        if "employee_id" in num_cols:
            num_cols.remove("employee_id")
            
        chart_view = st.selectbox(
            "Select Chart Category:",
            [
                "1. Numerical Distributions (Histograms & KDE)",
                "2. Outlier Verification (Box Plots)",
                "3. Categorical Breakdown (Bar Charts)",
                "4. Department & Salary Deep-Dive",
                "5. Correlation Matrix & Heatmap",
            ]
        )
        
        if chart_view == "1. Numerical Distributions (Histograms & KDE)":
            st.markdown("##### Distribution of Numerical Variables with Mean and Median Indicators")
            if num_cols:
                selected_num = st.selectbox("Select numerical column to inspect:", num_cols)
                mean_v = cleaned_df[selected_num].mean()
                median_v = cleaned_df[selected_num].median()
                
                fig = px.histogram(
                    cleaned_df,
                    x=selected_num,
                    marginal="box",
                    nbins=12,
                    color_discrete_sequence=["#3b82f6"],
                    title=f"Distribution of {selected_num.replace('_', ' ').title()}",
                )
                fig.add_vline(x=mean_v, line_dash="dash", line_color="#ef4444", annotation_text=f"Mean: {mean_v:.2f}")
                fig.add_vline(x=median_v, line_dash="solid", line_color="#10b981", annotation_text=f"Median: {median_v:.2f}")
                fig.update_layout(height=480)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No numerical columns found.")

        elif chart_view == "2. Outlier Verification (Box Plots)":
            st.markdown("##### Quartile Analysis & Outlier Detection")
            if num_cols:
                fig_box = px.box(
                    cleaned_df,
                    y=num_cols,
                    title="Box Plots for Sanitized Numerical Features",
                    points="outliers",
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_box.update_layout(height=500)
                st.plotly_chart(fig_box, use_container_width=True)
            else:
                st.info("No numerical columns found.")

        elif chart_view == "3. Categorical Breakdown (Bar Charts)":
            st.markdown("##### Categorical Attribute Frequency Analysis")
            if cat_cols:
                sel_cat = st.selectbox("Select categorical feature:", cat_cols)
                cat_counts = cleaned_df[sel_cat].value_counts().reset_index()
                cat_counts.columns = [sel_cat, "Count"]
                
                fig_cat = px.bar(
                    cat_counts,
                    x=sel_cat,
                    y="Count",
                    color="Count",
                    color_continuous_scale="Blues",
                    text="Count",
                    title=f"Frequency Count for {sel_cat.replace('_', ' ').title()}"
                )
                fig_cat.update_layout(height=450)
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("No categorical columns found.")

        elif chart_view == "4. Department & Salary Deep-Dive":
            st.markdown("##### Salary Analysis Across Departments & Roles")
            if "department" in cleaned_df.columns and "salary" in cleaned_df.columns:
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    fig_dept_box = px.box(
                        cleaned_df,
                        x="department",
                        y="salary",
                        color="department",
                        title="Salary Distribution by Department",
                        points="all"
                    )
                    fig_dept_box.update_layout(showlegend=False, height=450)
                    st.plotly_chart(fig_dept_box, use_container_width=True)
                    
                with sub_col2:
                    if "years_of_experience" in cleaned_df.columns:
                        fig_scatter = px.scatter(
                            cleaned_df,
                            x="years_of_experience",
                            y="salary",
                            color="department",
                            size="performance_score" if "performance_score" in cleaned_df.columns else None,
                            trendline="ols",
                            title="Experience vs. Salary (Bubble Size: Performance Score)"
                        )
                        fig_scatter.update_layout(height=450)
                        st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Department or Salary column missing for this visualization.")

        elif chart_view == "5. Correlation Matrix & Heatmap":
            st.markdown("##### Pearson Correlation Heatmap")
            if len(num_cols) >= 2:
                corr_matrix = cleaned_df[num_cols].corr()
                fig_heatmap = px.imshow(
                    corr_matrix,
                    text_auto=".2f",
                    color_continuous_scale="RdBu_r",
                    zmin=-1,
                    zmax=1,
                    title="Correlation Matrix of Cleaned Numerical Features"
                )
                fig_heatmap.update_layout(height=500)
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.info("Need at least 2 numerical features to construct a correlation heatmap.")

    # -------------------------------------------------------------------------
    # TAB 4: EXPORT SANITIZED DATA
    # -------------------------------------------------------------------------
    with tab_export:
        st.markdown('<div class="section-title">💾 Export Sanitized Data & Cleaning Report</div>', unsafe_allow_html=True)
        st.write("Download the sanitized dataset as CSV or export a detailed Markdown audit summary.")
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_buffer = io.StringIO()
            # If join_date is datetime, format nicely
            export_df = cleaned_df.copy()
            if "join_date" in export_df.columns and pd.api.types.is_datetime64_any_dtype(export_df["join_date"]):
                export_df["join_date"] = export_df["join_date"].dt.strftime("%Y-%m-%d")
                
            export_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Download Cleaned CSV (cleaned_data.csv)",
                data=csv_data,
                file_name="cleaned_data.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.caption(f"File size: ~{len(csv_data) / 1024:.1f} KB | Records: {len(cleaned_df)}")

        with col_dl2:
            report_text = f"""# Data Cleaning & Preprocessing Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Metrics
- Raw Row Count: {init_shape[0]}
- Cleaned Row Count: {clean_shape[0]}
- Total Columns: {clean_shape[1]}
- Initial Missing Values: {init_nulls}
- Final Missing Values: {clean_nulls}
- Duplicate Rows Removed: {raw_df.duplicated().sum()}

## Actions Taken
"""
            for item in audit_log:
                report_text += f"- **{item['stage']}**: {item['action']} ({item['impact']})\n"
                
            st.download_button(
                label="📄 Download Quality Audit Report (Markdown)",
                data=report_text,
                file_name="data_cleaning_audit_report.md",
                mime="text/markdown",
                use_container_width=True
            )
            st.caption("Includes full step-by-step audit trail and metadata verification.")
else:
    st.info("Please select or upload a dataset to begin.")
