import os
import sys
import streamlit as st

st.title("🔍 Server Diagnostic Tool")

st.subheader("1. Root Directory Files")
st.write(os.listdir('.'))

st.subheader("2. Modules Folder")
if os.path.exists('modules'):
    st.write(os.listdir('modules'))
else:
    st.error("🚨 The 'modules' folder is MISSING from the server!")

st.subheader("3. UI Folder")
if os.path.exists('ui'):
    st.write(os.listdir('ui'))
else:
    st.error("🚨 The 'ui' folder is MISSING from the server!")
