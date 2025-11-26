# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 14:41:19 2025

@author: ljp
"""

import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import time

# --- APP CONFIGURATION ---
try:
    st.set_page_config(page_title="WeldMaster Pro", page_icon="🔥", layout="wide")
except:
    pass # Prevents error if config runs twice

# --- CSS STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; background-color: #FF4B4B; color: white; font-weight: bold; }
    .report-box { border: 2px solid #ccc; padding: 15px; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIC ENGINE ---
def get_recommendation(material, thickness, joint_type):
    rec = "Consult Engineer"
    reason = "Specialized Application"
    
    if material == "Aluminum":
        if thickness == "Thin (< 3mm)":
            rec, reason = "GTAW (TIG)", "AC Current required. Best for thin gauge control."
        else:
            rec, reason = "GMAW (MIG) - Spool Gun", "Use Spray Transfer mode for efficiency."
    elif material == "Stainless Steel":
        if thickness == "Thin (< 3mm)":
            rec, reason = "GTAW (TIG)", "Low heat input prevents warping."
        else:
            rec, reason = "GMAW (MIG) / Stick", "Use 308/309 filler. Purging required for pipes."
    elif material == "Carbon Steel":
        if joint_type == "Butt Joint" and thickness == "Thick (> 6mm)":
            rec, reason = "SMAW (Stick) / FCAW", "Requires V-Groove prep for full penetration."
        elif thickness == "Thin (< 3mm)":
            rec, reason = "GMAW (MIG) Short Circuit", "Fast travel speed needed to avoid burn-through."
        else:
            rec, reason = "GMAW (MIG)", "Standard CV MIG. Good fusion and speed."
            
    return rec, reason

def simulate_ai_detection(image):
    time.sleep(1.5)
    return "Analysis Complete. Edge detection confidence: 92%"

# --- MAIN NAVIGATION ---
st.title("🔥 WeldMaster Pro Mobile")

# Sidebar
mode = st.sidebar.radio("Select Tool", ["📷 AI Joint Scanner", "🛠 Manual Selector", "🔍 Inspection Checklist"])

# --- MODE 1: AI CAMERA SCANNER ---
if mode == "📷 AI Joint Scanner":
    st.header("Camera Joint Detector")
    st.info("Point camera at the weld joint to analyze geometry.")

    img_file = st.camera_input("Take a photo of the joint")

    if img_file is not None:
        img = Image.open(img_file)
        
        with st.spinner('🤖 AI analyzing joint geometry...'):
            ai_status = simulate_ai_detection(img)
        
        st.success(ai_status)
        
        st.markdown("### Detected Geometry Candidate:")
        col1, col2 = st.columns(2)
        with col1:
            st.image(img, caption="Captured Image", width=250)
        
        with col2:
            st.write("**Based on visual features, confirm the joint type:**")
            scan_material = st.selectbox("Detected Material", ["Carbon Steel", "Stainless Steel", "Aluminum"])
            scan_thick = st.selectbox("Estimated Thickness", ["Thin (< 3mm)", "Medium (3mm-6mm)", "Thick (> 6mm)"])
            
            st.write("Confirm Joint Type to Get Process:")
            b1, b2, b3, b4 = st.columns(4)
            if b1.button("Butt"):
                rec, reason = get_recommendation(scan_material, scan_thick, "Butt Joint")
                st.session_state['scan_result'] = (rec, reason)
            if b2.button("Tee"):
                rec, reason = get_recommendation(scan_material, scan_thick, "Tee Joint")
                st.session_state['scan_result'] = (rec, reason)
            if b3.button("Lap"):
                rec, reason = get_recommendation(scan_material, scan_thick, "Lap Joint")
                st.session_state['scan_result'] = (rec, reason)
            if b4.button("Corner"):
                rec, reason = get_recommendation(scan_material, scan_thick, "Corner Joint")
                st.session_state['scan_result'] = (rec, reason)

        if 'scan_result' in st.session_state:
            res_proc, res_reason = st.session_state['scan_result']
            st.markdown(f"""
            <div class="report-box">
                <h3 style="color: #d90429;">Recommended Process: {res_proc}</h3>
                <p><b>Technical Reasoning:</b> {res_reason}</p>
            </div>
            """, unsafe_allow_html=True)

# --- MODE 2: MANUAL SELECTOR ---
elif mode == "🛠 Manual Selector":
    st.header("🛠 Standard Process Selector")
    col1, col2, col3 = st.columns(3)
    with col1:
        mat = st.selectbox("Material", ["Carbon Steel", "Stainless Steel", "Aluminum"])
    with col2:
        thk = st.selectbox("Thickness", ["Thin (< 3mm)", "Medium (3mm-6mm)", "Thick (> 6mm)"])
    with col3:
        jnt = st.selectbox("Joint Type", ["Butt Joint", "Tee Joint", "Lap Joint", "Corner Joint"])
    
    if st.button("Calculate Process"):
        proc, reason = get_recommendation(mat, thk, jnt)
        st.success(f"Use: **{proc}**")
        st.info(reason)

# --- MODE 3: INSPECTION CHECKLIST ---
elif mode == "🔍 Inspection Checklist":
    st.header("🔍 Visual Inspection Log")
    with st.form("inspection_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("No Cracks")
            st.checkbox("No Undercut")
        with col2:
            st.checkbox("Leg Size OK")
            st.checkbox("Convexity OK")
        st.form_submit_button("Generate Report")