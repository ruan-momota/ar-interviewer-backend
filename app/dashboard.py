import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:8000/v1"

st.set_page_config(
    page_title="AR Interviewer Admin",
    page_icon="🤖",
    layout="wide"
)

def fetch_interviews():
    try:
        response = requests.get(f"{API_BASE_URL}/admin/interviews")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch interviews: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Connection error: {e}")
        return []

def fetch_interview_detail(session_id):
    """get details of single interview"""
    try:
        response = requests.get(f"{API_BASE_URL}/admin/interviews/{session_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch details")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

st.sidebar.title("🔍 Interview Selection")

interviews = fetch_interviews()

if not interviews:
    st.sidebar.warning("No history")
    selected_session_id = None
else:
    options = {
        f"{i['candidate_name']} - {i['job_title']} ({i['start_time'][:10]})": i['id'] 
        for i in interviews
    }
    
    selected_label = st.sidebar.selectbox(
        "Choose one to see the detail:",
        options=list(options.keys())
    )
    selected_session_id = options[selected_label]

    st.sidebar.markdown("---")
    st.sidebar.info(f"Total Sessions: {len(interviews)}")

if selected_session_id:
    data = fetch_interview_detail(selected_session_id)
    
    if data:
        st.title(f"📄 Interview Details: {data['candidate_name']}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Job Position", data['job_title'])
        with col2:
            st.metric("Status", data['status'].upper())
        with col3:
            score = data.get('score', 0)
            delta_color = "normal"
            if score >= 80: delta_color = "normal"
            elif score < 60: delta_color = "inverse"
            st.metric("Score", f"{score}/100", delta_color=delta_color)
        with col4:
            st.metric("Date", data['start_time'][:16].replace("T", " "))

        st.divider()

        tab_chat, tab_report, tab_raw = st.tabs(["💬 Transcript", "📊 Report", "ℹ️ Raw Data"])

        with tab_chat:
            messages = data.get('messages', [])
            
            if not messages:
                st.info("No history")
            
            for msg in messages:
                role = msg['role']
                content = msg['content']
                time_str = msg.get('time', '')[:16].replace("T", " ")

                if role == "system":
                    with st.expander(f"⚙️ System Prompt ({time_str})"):
                        st.caption(content)
                
                elif role == "assistant":
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(content)
                        st.caption(f"Interviewer - {time_str}")
                
                elif role == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.write(content)
                        st.caption(f"Candidate - {time_str}")

        with tab_report:
            report = data.get('report')
            if not report:
                st.warning("⚠️ No report")
            else:
                st.subheader("💡 Feedback Summary")
                st.info(report.get('feedback_summary', 'None'))

                r_col1, r_col2 = st.columns(2)
                
                with r_col1:
                    st.subheader("✅ Strengths")
                    for s in report.get('strengths', []):
                        st.success(f"- {s}")
                        
                with r_col2:
                    st.subheader("🚀 Areas for Improvement")
                    for area in report.get('areas_for_improvement', []):
                        st.warning(f"- {area}")

                st.subheader("🎯 Next Mission")
                st.error(f"👉 {report.get('mission', 'None')}")

        with tab_raw:
            st.json(data)

else:
    st.title("👋 AR Interviewer Console")
    st.markdown("""
    请从左侧侧边栏选择一个面试会话以查看详情。
    
    **Functions:**
    - Transcripts
    - Report
    - Interview States
    """)