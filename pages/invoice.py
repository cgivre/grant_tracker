import logging
import os
from pprint import pprint

import dateparser
import pandas as pd
import streamlit as st

from utils.ai_utils import AIUtils
from utils.utils import Utils
from pathlib import Path

st.set_page_config(layout="wide")
streamlit_root_logger = logging.getLogger(__name__)

utils = Utils()
ai_utils = AIUtils()

st.session_state["grants"] = utils.get_grants()
grants = st.session_state["grants"]

# Add id
grants["id"] = grants.index


def process_file(grant: str):
    if st.session_state['uploaded_invoice'] is None:
        return

    streamlit_root_logger.debug(f"Uploaded File: {st.session_state['uploaded_invoice']}")
    save_folder = f"./invoice_images/{grant}/"
    save_path = Path(save_folder, st.session_state['uploaded_invoice'].name)

    path_exists = os.path.exists(save_folder)
    if not path_exists:
        # Create a new directory because it does not exist
        os.makedirs(save_folder)

    streamlit_root_logger.debug(f"Saved File: {save_path}")
    with open(save_path, mode='wb') as w:
        w.write(st.session_state['uploaded_invoice'].getvalue())

    if save_path.exists() and save_path.is_file():
        st.toast(f"Invoice has been uploaded.")

        # Now analyze the invoice
        st.session_state['parsed_invoice'] = ai_utils.analyze_image(save_path)


with st.container():
    st.markdown("Please select a grant.")
    selected_grant = st.selectbox(label="Select Grant", options=grants['grant_name'])

    invoice_image = st.file_uploader(label="Upload Invoice",
                                     key='uploaded_invoice',
                                     type=['png', 'jpg', 'jpeg', 'pdf'],
                                     accept_multiple_files=False,
                                     on_change=process_file, args=(selected_grant,))

    with st.form("invoice_form", clear_on_submit=True):

        vendor_name = st.text_input(label="Vendor Name",
                                    value='' if 'parsed_invoice' not in st.session_state.keys() else
                                    st.session_state['parsed_invoice']['invoice_information']['vendor_name']
                                    )

        if selected_grant != '':
            start_date = pd.to_datetime(
                str(grants[grants['grant_name'] == selected_grant]['grant_start_date'].values[0]))
            end_date = pd.to_datetime(str(grants[grants['grant_name'] == selected_grant]['grant_end_date'].values[0]))

            expense_categories = st.multiselect(label="Grant Categories",
                                                help="Enter the categories of your expense.",
                                                options=['Early Childhood', 'Education',
                                                         'General Purpose', 'Food', 'Security',
                                                         'Transportation'])
            invoice_date = st.date_input('Invoice Date',
                                         min_value=start_date,
                                         value=dateparser.parse(str(start_date)) if 'parsed_invoice' not in st.session_state.keys() else
                                         dateparser.parse(st.session_state['parsed_invoice']['invoice_information']['invoice_date'])
                                         )
            invoice_amount = st.number_input(label="Amount", min_value=0.0,
                                             max_value=
                                             grants[grants['grant_name'] == selected_grant]['grant_amount'].values[
                                                 0].astype(float),
                                             step=100.00,
                                             value=0.0 if 'parsed_invoice' not in st.session_state.keys() else
                                             st.session_state['parsed_invoice']['invoice_information']['invoice_amount']
                                             )
            invoice_description = st.text_area(label="Invoice Description",
                                               value='' if 'parsed_invoice' not in st.session_state.keys() else
                                               st.session_state['parsed_invoice']['invoice_information']['description'])

            submitted = st.form_submit_button("Submit")

            # Process form submission
            if submitted:
                utils.create_invoice(selected_grant, vendor_name, Utils.list_to_string(expense_categories),
                                     invoice_date,
                                     invoice_amount, invoice_description, "invoice_image")

