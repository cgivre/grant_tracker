import pandas as pd

import streamlit as st
import dateparser
st.set_page_config(layout="wide")

try:
    grants = pd.read_csv('static/data/grants.csv')
    # Add id
    grants["id"] = grants.index

except:
    grants = pd.DataFrame()

with st.container():
    with st.form("invoice_form", clear_on_submit=True):
        selected_grant = st.selectbox(label="Select Grant", options=grants['grant_name'])
        vendor_name = st.text_input(label="Vendor Name")

        if selected_grant != '':
            start_date = dateparser.parse(grants[grants['grant_name'] == selected_grant]['grant_start_date'].values[0])
            end_date = dateparser.parse(grants[grants['grant_name'] == selected_grant]['grant_end_date'].values[0])

            expense_categories = st.multiselect(label="Grant Categories",
                                              help="Enter the categories of your expense.",
                                              options=['Early Childhood', 'Education',
                                                       'General Purpose', 'Food', 'Security',
                                                       'Transportation'])

            invoice_date = st.date_input('Invoice Date',
                                         min_value=start_date, max_value=end_date)
            invoice_amount = st.number_input(label="Amount", min_value=0.0,
                                             max_value=grants[grants['grant_name'] == selected_grant]['grant_amount'].values[0].astype(float),
                                             )
            invoice_image = st.file_uploader(label="Upload Invoice", type=['png', 'jpg', 'jpeg', 'pdf'])

            st.form_submit_button("Submit")

