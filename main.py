import logging

import pandas as pd

import streamlit as st
from db_utils import utils

st.set_page_config(layout="wide")

utils = utils.Utils()
updated_df = None

if "grants" not in st.session_state:
    grants = utils.get_grants()
    # Add id
    grants["id"] = grants.index
    # Add link to add invoice
    grants['invoice_link'] = f'#' + grants['id'].astype(str)
    st.session_state["grants"] = grants


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


# Add metric columns
col1, col2 = st.columns(2)
col1.metric(
    label="Active Grants",
    help="Number of grants that are active.",
    value=len(st.session_state["grants"])
)
col2.metric(
    label="Total Available Funds",
    help="Total amount of available funds",
    value=utils.get_total_available_grants(),
)

if len(st.session_state["grants"]) > 0:
    updated_df = st.data_editor(data=st.session_state["grants"],
                                use_container_width=True,
                                hide_index=True,
                                num_rows="dynamic")

if st.button("Add Grant"):
    create_grant()


if updated_df is not None and not updated_df.equals(st.session_state["grants"]):
    # This will only run if
    # 1. Some widget has been changed (including the dataframe editor), triggering a
    # script rerun, and
    # 2. The new dataframe value is different from the old value
    # update(updated_df)
    logging.debug("Updating main dataframe.")
    st.session_state["grants"] = updated_df
