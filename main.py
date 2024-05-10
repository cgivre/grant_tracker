import pandas as pd

import streamlit as st
st.set_page_config(layout="wide")

try:
    grants = pd.read_csv('static/data/grants.csv')
    # Add id
    grants["id"] = grants.index
    # Add link to add invoice
    grants['invoice_link'] = f'#' + grants['id'].astype(str)

except:
    grants = pd.DataFrame()


def update_grants() -> pd.DataFrame:
    global grants
    return grants


def record_grant(grant_name: str, grant_description: str,
                 grant_duration: str, grant_amount: float, grant_categories: list) -> pd.DataFrame:
    global grants

    # TODO Validate Data

    # Create a dictionary
    grant = {
        "grant_name": grant_name,
        "grant_description": grant_description,
        "grant_start_date": grant_duration[0],
        "grant_end_date": grant_duration[1],
        "grant_amount": grant_amount,
        "grant_categories": str(grant_categories)
    }
    temp_df = pd.DataFrame([grant])
    grants = pd.concat([grants, temp_df])
    grants.to_csv('grants.csv', index=False)
    return grants


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
            global grants
            grants = record_grant(grant_name, grant_description, grant_duration, grant_amount, grant_categories)
            st.rerun()



if len(grants) > 0:
    updated_df = st.data_editor(data=grants, use_container_width=True, hide_index=True, num_rows="dynamic")

if st.button("Add Grant"):
    create_grant()
