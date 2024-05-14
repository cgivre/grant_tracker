import logging

import streamlit as st
import dateparser

from db_utils.utils import Utils

st.set_page_config(layout="wide")
streamlit_root_logger = logging.getLogger(st.__name__)

utils = Utils()


st.session_state["grants"] = utils.get_grants()
grants = st.session_state["grants"]

# Add id
grants["id"] = grants.index


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
                                             step=100.00
                                             )
            invoice_description = st.text_area(label="Invoice Description")
            invoice_image = st.file_uploader(label="Upload Invoice",
                                             type=['png', 'jpg', 'jpeg', 'pdf'],
                                             accept_multiple_files=False)

            submitted = st.form_submit_button("Submit")

            # Process form submission
            if submitted:
                utils.create_invoice(selected_grant, vendor_name, Utils.list_to_string(expense_categories), invoice_date,
                                     invoice_amount, invoice_description, "invoice_image")


