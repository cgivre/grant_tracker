import os

import pandas as pd
import dateparser
from streamlit.logger import get_logger
import streamlit as st
from utils import utils
from pathlib import Path

from utils.ai_utils import AIUtils

st.set_page_config(layout="wide")
streamlit_logger = get_logger(__name__)


utils = utils.Utils()
ai_utils = AIUtils()

updated_df = None

grants = utils.get_grants()
grants['remaining_funds'] = grants['grant_amount'] - grants['invoiced_total']
grants['remaining_percentage'] = grants['remaining_funds'] / grants['grant_amount'] * 100

grants['time_remaining_percentage'] = (grants['days_remaining'] / grants['total_duration'] * 100)

# The time remaining should never be a negative number, so if the grant is done, replace with zero.
grants['time_remaining_percentage'].mask(grants['time_remaining_percentage'] < 0, 0, inplace=True)
grants['health_score'] = 1 / (
        (grants['remaining_funds'] / grants['grant_amount']) * (grants['days_elapsed'] / grants['total_duration']))

st.session_state["grants"] = grants


@st.experimental_dialog("Are you sure?")
def delete_grant(grant_id: int, grant_name: str):
    st.write(f"Clicking Yes will permanently delete all invoices associated with {grant_name}. Are you "
             f"sure you wish to proceed?")
    dialog_col_1, dialog_col_2 = st.columns(2)
    if dialog_col_1.button("Yes"):
        result = utils.process_grant_deletion(grant_id, grant_name)
        st.rerun()
    elif dialog_col_2.button("No"):
        st.rerun()


@st.experimental_dialog("Record a Grant")
def create_grant():
    st.header("Enter a Grant")
    with st.form(key="create_grant", clear_on_submit=True):
        grant_name = st.text_input(label="Grant Name",
                                   placeholder="Enter the Grant Name",
                                   help="Enter a Grant Name")
        grant_description = st.text_area(label="Grant Description",
                                         placeholder="Enter a brief description of the grant.",
                                         help="Enter a brief description of the grant.",
                                         )

        grant_duration = st.date_input(label="Grant Duration",
                                       help="Enter the start and end dates for your grant.",
                                       value=[])
        grant_amount = st.number_input(label="Grant Amount",
                                       help="Enter the amount of the grant.",
                                       placeholder="Enter the amount of the grant.",
                                       min_value=0,
                                       step=100)
        grant_categories = st.multiselect(label="Grant Categories",
                                          help="Enter the categories of your grant.",
                                          options=['Early Childhood', 'Education',
                                                   'General Purpose', 'Food', 'Security',
                                                   'Transportation'])
        submitted = st.form_submit_button("Submit Grant")
        if submitted:
            utils.create_grant(grant_name, grant_description, grant_duration[0], grant_duration[1], grant_amount,
                               grant_categories)
            st.session_state["grants"] = utils.get_grants()

            st.rerun()


def process_image_file(grant: str) -> None:
    """
    This function processes an image file. It accepts an input file, uploads that file and processes it,
    :param grant: The grant name for which the image is associated.
    """
    if st.session_state['uploaded_invoice'] is None:
        return

    streamlit_logger.debug(f"Uploaded File: {st.session_state['uploaded_invoice']}")

    hashed_folder = utils.get_hashed_folder(grant)

    save_folder = f"./invoice_images/{hashed_folder}/"
    save_path = Path(save_folder, st.session_state['uploaded_invoice'].name)

    path_exists = os.path.exists(save_folder)
    if not path_exists:
        # Create a new directory because it does not exist
        os.makedirs(save_folder)

    streamlit_logger.debug(f"Saved File: {save_path}")
    with open(save_path, mode='wb') as w:
        w.write(st.session_state['uploaded_invoice'].getvalue())

    if save_path.exists() and save_path.is_file():
        st.toast(f"Invoice has been uploaded.")

        # Now analyze the invoice
        st.session_state['parsed_invoice'] = ai_utils.analyze_image(save_path)


# Add messages here
if 'success_message' in st.session_state.keys() and st.session_state['success_message'] is not None:
    st.success(st.session_state['success_message'])
    st.session_state['success_message'] = ''

# Add metric columns
col1, col2, col3 = st.columns(3)
col1.metric(
    label="Active Grants",
    help="Number of grants that are active.",
    value=len(st.session_state["grants"])
)
col2.metric(
    label="Total Grant Funds",
    help="Total amount of available funds",
    value=utils.get_total_available_grants(),
)

col3.metric(
    label="Total Unclaimed Funding",
    help="Amount of funding which has not been claimed.",
    value=utils.get_available_funding()
)

if len(st.session_state["grants"]) > 0:
    grant_selection = st.dataframe(data=st.session_state["grants"],
                                   key="grant_data",
                                   hide_index=True,
                                   use_container_width=True,
                                   on_select="rerun",
                                   column_order=['grant_name', 'health_score', 'grant_amount', 'remaining_funds',
                                                 'remaining_percentage', 'time_remaining_percentage',
                                                 'grant_start_date', 'grant_end_date', 'grant_categories'],
                                   column_config={
                                       "grant_name": st.column_config.TextColumn(label="Grant Name",
                                                                                 help="The name of the grant"),
                                       "grant_amount": st.column_config.NumberColumn(label="Grant Amount",
                                                                                     help="The total amount of funding available for this grant.",
                                                                                     format="$%.2f"),

                                       "health_score": st.column_config.NumberColumn(label="Grant Health Score"),
                                       "grant_categories": st.column_config.ListColumn(label="Grant Categories", ),
                                       "grant_start_date": st.column_config.DateColumn(label="Grant Start Date",
                                                                                       format="MMM Do, YYYY"),
                                       "grant_end_date": st.column_config.DateColumn(label="Grant End Date",
                                                                                     format="MMM Do, YYYY"),
                                       "remaining_funds": st.column_config.NumberColumn(label="Remaining Funds",
                                                                                        help="The total amount of funding remaining for this grant.",
                                                                                        format="$%.2f"),
                                       "time_remaining_percentage": st.column_config.ProgressColumn(
                                           "Time Remaining",
                                           help="The number of days remaining for this grant.",
                                           format="%.1f",
                                           min_value=0,
                                           max_value=100,
                                       ),
                                       "remaining_percentage": st.column_config.ProgressColumn(
                                           label="Funding Remaining",
                                           help="The percentage of the grant that is available.",
                                           format="%.1f",
                                           min_value=0,
                                           max_value=100,
                                       )
                                   },
                                   selection_mode=["single-row"], )

if st.button("Add Grant"):
    create_grant()

# If the user has selected a grant, display the grant info tabs
if len(grant_selection.selection['rows']) > 0:
    # Now get the grant data.
    grant_info = st.session_state["grants"].iloc[grant_selection.selection['rows'][0]]
    grant_info_tab, invoices_tab, add_invoice_tab = st.tabs(["Grant Information", "Invoices", "Add Invoice"])

    # TODO Make this pretty
    grant_info_tab.write(grant_info)

    button_col1, button_col2 = grant_info_tab.columns(2)

    button_col1.button("Update Grant")
    if button_col2.button("Delete Grant"):
        if delete_grant(grant_info['grant_id'], grant_info['grant_name']):
            st.session_state['success_message'] = f"Grant {grant_info['grant_name']} has been deleted."

    # Invoice Tab
    invoice_data = utils.get_invoices(grant_info['grant_id'])
    invoices_tab.dataframe(
        data=invoice_data,
        hide_index=True,
        use_container_width=True,
    )

    # Add Invoice tab
    invoice_image = add_invoice_tab.file_uploader(label="Upload Invoice",
                                                  key='uploaded_invoice',
                                                  type=['png', 'jpg', 'jpeg', 'pdf'],
                                                  accept_multiple_files=False,
                                                  on_change=process_image_file, args=(grant_info['grant_name'],))

    with add_invoice_tab.form("invoice_form", clear_on_submit=True):

        vendor_name = st.text_input(label="Vendor Name",
                                    value='' if 'parsed_invoice' not in st.session_state.keys() else
                                    st.session_state['parsed_invoice']['invoice_information']['vendor_name']
                                    )

        if grant_info['grant_name'] != '':
            start_date = pd.to_datetime(
                str(grants[grants['grant_name'] == grant_info['grant_name']]['grant_start_date'].values[0]))
            end_date = pd.to_datetime(
                str(grants[grants['grant_name'] == grant_info['grant_name']]['grant_end_date'].values[0]))

            expense_categories = st.multiselect(label="Grant Categories",
                                                help="Enter the categories of your expense.",
                                                options=['Early Childhood', 'Education',
                                                         'General Purpose', 'Food', 'Security',
                                                         'Transportation'])
            invoice_date = st.date_input('Invoice Date',
                                         min_value=start_date,
                                         value=dateparser.parse(
                                             str(start_date)) if 'parsed_invoice' not in st.session_state.keys() else
                                         dateparser.parse(
                                             st.session_state['parsed_invoice']['invoice_information']['invoice_date'])
                                         )
            invoice_amount = st.number_input(label="Amount", min_value=0.0,
                                             max_value=
                                             grants[grants['grant_name'] == grant_info['grant_name']][
                                                 'grant_amount'].values[
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
                utils.create_invoice(grant_info['grant_name'], vendor_name, utils.list_to_string(expense_categories),
                                     invoice_date,
                                     invoice_amount, invoice_description, "invoice_image")
