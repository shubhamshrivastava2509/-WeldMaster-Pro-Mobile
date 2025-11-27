# -*- coding: utf-8 -*-
"""
Created on Thu Nov 27 10:20:28 2025

@author: ljp
"""

import streamlit as st
import json
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from google.genai.errors import APIError

# --- Configuration ---
# Set the page configuration for a mobile-friendly, wide layout
st.set_page_config(
    page_title="AI weld Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize the Gemini client (assumes API key is set in environment or secrets)
try:
    client = genai.Client()
except Exception:
    # If the client cannot be initialized (e.g., API key missing), use a placeholder client
    # Define a dummy client structure to allow the rest of the code to run
    class DummyClient:
        def generate_content(self, model, contents, config=None, system_instruction=None):
            raise APIError("Gemini API key not found or client failed to initialize.")
    client = DummyClient()


# --- Custom CSS for Crimson Shading and Theme ---
def inject_custom_css():
    """Injects CSS for the crimson shaded background, logo, and overall theme."""
    st.markdown("""
        <style>
        /* Crimson Radial Gradient Shading for Background */
        body {
            color: #f8f8f8;
        }
        .stApp {
            background: radial-gradient(circle at center, #660011 0%, #3f000a 80%, #290007 100%);
            color: #f8f8f8;
        }

        /* Container Styling */
        .stContainer, .stFileUploader, .stButton > button {
            background-color: #590011 !important; /* Slightly lighter crimson card background */
            border: 1px solid #7d0016 !important;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
            color: #f8f8f8 !important;
        }
       
        /* Analyze Button Styling (Crimson) */
        #analyze_weld_btn {
            background-color: #f87171;
            color: white;
            font-weight: bold;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.75rem;
            transition: all 0.2s;
        }
        #analyze_weld_btn:hover {
            background-color: #ef4444;
        }
       
        /* PDF Download Button Styling (Blue Accent) */
        #download_pdf_btn {
            background-color: #38bdf8;
            color: white;
            font-weight: bold;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.75rem;
            transition: all 0.2s;
        }
        #download_pdf_btn:hover {
            background-color: #0c9fec;
        }

        /* Styling for the Weak Area Box in Results */
        .weak-area-box {
            background-color: #7d0016; /* Darker Crimson Background for highlight */
            border-left: 4px solid #ff4d4d; /* Bright Red border for highlight */
            padding: 1rem;
            border-radius: 0.5rem;
            margin-top: 0.75rem;
        }

        /* Custom List Styles (for list items) */
        ul.custom-list {
            list-style: none;
            padding-left: 0;
            margin-top: 0.5rem;
        }
        ul.custom-list li {
            padding-left: 1.5em;
            text-indent: -1.5em;
            margin-bottom: 0.25rem;
            color: #ccc;
        }
        ul.custom-list li::before {
            content: "•";
            color: #f87171; /* Crimson accent color for bullets */
            font-weight: bold;
            display: inline-block;
            width: 1.5em;
        }
       
        /* General Streamlit tweaks for text contrast */
        h1, h2, h3, h4 {
            color: #fff;
        }
        .stMarkdown p, .stMarkdown li, .stMarkdown div, .stFileUploader label, .stCameraInput label {
            color: #f8f8f8 !important;
        }
        .st-emotion-cache-r42sng a {
            color: #38bdf8 !important;
        }
        </style>
        """, unsafe_allow_html=True)

inject_custom_css()

# --- Logo and Header ---
WELDING_LOGO_SVG = """
<div style="text-align: center;">
    <svg width="60" height="60" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Welding Helmet Outline -->
        <path d="M75 50L60 35C60 30 50 25 50 25L25 50L75 50Z" fill="#ff4d4d" opacity="0.8"/>
        <path d="M25 50C20 50 15 55 15 60V80H85V60C85 55 80 50 75 50H25Z" fill="#4b5563"/>
        <!-- Eye Shield/Filter -->
        <rect x="35" y="55" width="30" height="15" rx="2" fill="#000000"/>
        <!-- Arc Spark/Analysis Glow -->
        <circle cx="50" cy="50" r="5" fill="#f8d743" opacity="1"/>
        <!-- Torch/Analysis Beam -->
        <line x1="85" y1="65" x2="105" y2="65" stroke="#f8d743" stroke-width="4" stroke-linecap="round"/>
    </svg>
</div>
"""

st.markdown(WELDING_LOGO_SVG, unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: white;'>WELD AI ANALYZER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #ccc; margin-bottom: 2rem;'>Detailed inspection using Gemini's vision capabilities and report generation.</p>", unsafe_allow_html=True)


# --- Gemini API Call Logic (Python SDK) ---

def call_gemini_api(prompt: str, image_bytes: bytes):
    """
    Calls the Gemini API to analyze the weld image.
    """
    st.session_state.analysis_running = True
   
    # Define the JSON schema for structured output
    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "weldJointType": types.Schema(type=types.Type.STRING, description="The identified type of weld joint (e.g., Butt, Lap, Corner, Tee, Edge)."),
            "weldProcessDescription": types.Schema(type=types.Type.STRING, description="A brief, detailed description (2-4 sentences) of the assumed welding process, joint preparation, and joint position."),
            "dimensionToMeasure": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING), description="List of key dimensions that should be measured."),
            "defectPrediction": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING), description="List of potential or predicted defects visible in the image."),
            "dimensionEstimation": types.Schema(type=types.Type.STRING, description="A descriptive estimate of a primary dimension and what reference point was used for scaling."),
            "weakJointAreaDescription": types.Schema(type=types.Type.STRING, description="A detailed text description specifying the physical location and reason for the most likely weak joint area.")
        },
        required=["weldJointType", "weldProcessDescription", "dimensionToMeasure", "defectPrediction", "dimensionEstimation", "weakJointAreaDescription"]
    )
   
    system_instruction = ("You are a certified welding inspector (CWI) and AI assistant specializing in image analysis. "
                          "Your task is to analyze an image of a weld joint. Respond ONLY with a valid JSON object matching the provided schema. "
                          "Be specific and use correct welding terminology.")

    try:
        # Load the image using PIL
        image_part = Image.open(BytesIO(image_bytes))

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema
        )
       
        contents = [image_part, prompt]

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=config,
            system_instruction=system_instruction
        )
       
        # Parse the JSON string from the response
        return json.loads(response.text)

    except APIError as e:
        st.error(f"Gemini API Error: {e.message}. Check your API key and permissions.")
        return None
    except json.JSONDecodeError:
        st.error("Error: Failed to parse structured JSON response from the model.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during analysis: {e}")
        return None
    finally:
        st.session_state.analysis_running = False


# --- Streamlit UI and State Management ---

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if 'analysis_running' not in st.session_state:
    st.session_state.analysis_running = False
   
# Use a centered container for the mobile-like layout
col1, col2, col3 = st.columns([1, 4, 1])

with col2:
    # --- Input Tabs: Camera vs. Upload ---
    st.markdown("## 📷 Image Input", unsafe_allow_html=True)
   
    tab_capture, tab_upload = st.tabs(["Capture Photo", "Upload File"])
   
    captured_photo = None
    uploaded_file = None

    with tab_capture:
        # Live camera access
        captured_photo = st.camera_input("Take a photo of the weld joint")

    with tab_upload:
        # File upload access
        uploaded_file = st.file_uploader(
            "Upload an existing weld image (JPG or PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=False,
            help="Upload an image from your device storage."
        )

    # Determine the file source for analysis
    file_source = captured_photo if captured_photo is not None else uploaded_file
   
    if file_source is not None:
        # Display the selected image (from camera or upload)
        st.image(file_source, caption='Weld Image Preview', use_container_width=True)

        # --- Analysis Button ---
        analyze_button_clicked = st.button(
            "Analyze Weld Joint",
            key='analyze_weld_btn',
            disabled=st.session_state.analysis_running,
            use_container_width=True
        )

        if analyze_button_clicked:
            # Read image bytes
            image_bytes = file_source.read()
            prompt = "Analyze this image of a weld joint. Provide a detailed analysis including dimensional estimates and a specific description of any visually observed weak joint area."
           
            with st.spinner('Analyzing weld joint with Gemini AI...'):
                result = call_gemini_api(prompt, image_bytes)
                if result:
                    st.session_state.analysis_result = result
                    st.toast("Analysis Complete!", icon="✅")
                else:
                    st.session_state.analysis_result = None
    else:
        st.session_state.analysis_result = None
        st.session_state.analysis_running = False
        st.info("Select the 'Capture Photo' tab to use your device's camera, or 'Upload File' to select an existing image.")

    # --- Results Display and PDF Report ---
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
       
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## Analysis Results", unsafe_allow_html=True)
       
        # 1. Joint Type & Dimensions
        st.markdown("### 1. Joint Type & Dimensions", unsafe_allow_html=True)
        st.markdown(f"**Predicted Joint Type:** <span style='color: #f87171;'>{result['weldJointType']}</span>", unsafe_allow_html=True)

        st.markdown(f"""
            <div style='background-color: #7d0016; padding: 1rem; border-radius: 0.5rem; margin-top: 0.5rem;'>
                <p style='color: #fff; font-weight: bold;'>Dimension Estimation:</p>
                <p style='color: #ccc; white-space: pre-line;'>{result['dimensionEstimation']}</p>
                <p style='color: #ffd700; font-size: 0.8rem; margin-top: 0.5rem;'>NOTE: True measurement requires a physical reference (ruler/coin) in the image.</p>
            </div>
        """, unsafe_allow_html=True)
       
        st.markdown("<p style='font-weight: bold; margin-top: 1rem;'>Key Measurements Required:</p>", unsafe_allow_html=True)
        st.markdown("<ul class='custom-list'>" + "".join([f"<li>{dim}</li>" for dim in result['dimensionToMeasure']]) + "</ul>", unsafe_allow_html=True)


        # 2. Weak Area & Defect Prediction
        st.markdown("### 2. Weak Area & Defect Prediction", unsafe_allow_html=True)
       
        st.markdown(f"""
            <div class='weak-area-box'>
                <p style='font-weight: bold; color: #ff4d4d;'>Potential Weak Joint Area:</p>
                <p style='color: #ccc; white-space: pre-line;'>{result['weakJointAreaDescription']}</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<p style='font-weight: bold; margin-top: 1rem;'>Predicted Defects:</p>", unsafe_allow_html=True)
        st.markdown("<ul class='custom-list'>" + "".join([f"<li>{defect}</li>" for defect in result['defectPrediction']]) + "</ul>", unsafe_allow_html=True)

        # 3. Process & Position Description
        st.markdown("### 3. Process & Position Description", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #ccc; white-space: pre-line;'>{result['weldProcessDescription']}</p>", unsafe_allow_html=True)


        # --- Report Generation (Download Button) ---
       
        # Assemble the full report content as a downloadable string
        report_content = f"""
WELD INSPECTION REPORT
Date: {st.session_state.get('uploaded_time', 'N/A')}

1. JOINT TYPE & DIMENSIONS
Predicted Joint Type: {result['weldJointType']}

Dimension Estimation:
{result['dimensionEstimation']}

Key Measurements Required:
- {'\n- '.join(result['dimensionToMeasure'])}

2. WEAK AREA & DEFECT PREDICTION
Potential Weak Joint Area:
{result['weakJointAreaDescription']}

Predicted Defects:
- {'\n- '.join(result['defectPrediction'])}

3. PROCESS & POSITION DESCRIPTION
{result['weldProcessDescription']}
"""
       
        st.download_button(
            label="Download PDF Report (Text File)",
            data=report_content,
            file_name="Weld_Analysis_Report.txt", # Use TXT for maximum compatibility
            mime="text/plain",
            key='download_pdf_btn',
            use_container_width=True
        )

        st.markdown(
            "<p style='text-align: center; font-size: 0.8rem; color: #aaa; margin-top: 0.5rem;'>For a visual PDF, use your browser's 'Print to PDF' feature (Ctrl+P or Cmd+P).</p>",
            unsafe_allow_html=True
        )