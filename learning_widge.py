import streamlit as st
from streamlit_elements import elements, mui, sync

if "counter" not in st.session_state:
    st.session_state.counter = 0

with elements("counter_dashboard"):
    mui.Typography(f"Count: {st.session_state.counter}", variant="h4")

    # We use a lambda to increment the value, 
    # then sync() (with no args) to trigger the rerun.
    mui.Button(
        "Increment Now", 
        variant="contained", 
        onClick=lambda: [
            st.session_state.update({"counter": st.session_state.counter + 1}),
            sync() 
        ]
    )