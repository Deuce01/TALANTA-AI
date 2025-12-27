import streamlit as st
import google.genai as genai
import os
from dotenv import load_dotenv
from pypdf import PdfReader

# Load environment variables
load_dotenv()

# Professional CSS styling with mobile responsiveness
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1f4e79;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
        text-align: center;
    }
    .profile-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f4e79;
        margin-bottom: 1rem;
    }
    .chat-container {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-top: 1rem;
    }
    .stButton > button {
        background-color: #1f4e79;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .stSelectbox > div > div {
        background-color: white;
    }
    .upload-section {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        border: 1px dashed #1f4e79;
    }
    .status-success {
        background: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        margin-top: 0.5rem;
    }
    
    /* Mobile Responsive Styles */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
            margin-bottom: 0.3rem;
        }
        .sub-header {
            font-size: 1rem;
            margin-bottom: 1rem;
        }
        .profile-section {
            padding: 1rem;
            margin-bottom: 0.5rem;
        }
        .chat-container {
            padding: 0.5rem;
            margin-top: 0.5rem;
        }
        .stButton > button {
            padding: 0.4rem 0.8rem;
            font-size: 0.9rem;
        }
        .upload-section {
            padding: 0.8rem;
        }
        .css-1d391kg {
            padding-top: 1rem;
        }
        .stChatInput {
            margin-bottom: 1rem;
        }
        .row-widget.stHorizontal {
            flex-direction: column;
        }
        .row-widget.stHorizontal > div {
            width: 100% !important;
            margin-bottom: 0.5rem;
        }
    }
    
    @media (max-width: 480px) {
        .main-header {
            font-size: 1.8rem;
        }
        .sub-header {
            font-size: 0.9rem;
        }
        .profile-section {
            padding: 0.8rem;
        }
        .chat-container {
            padding: 0.3rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def extract_text_from_pdf(uploaded_file):
    if uploaded_file is not None:
        try:
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception:
            return None
    return None

def career_advisor_tab():
    # Custom icon in header
    icon_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="60" height="60" style="margin-bottom: 1rem;">
      <circle cx="256" cy="256" r="256" fill="#ffffff"/>
      <path d="M256 64 C150 64, 96 150, 96 220 C96 350, 180 410, 256 448 C332 410, 416 350, 416 220 C416 150, 362 64, 256 64 Z" fill="#000000"/>
      <path d="M256 64 C150 64, 96 150, 96 220 C96 350, 180 410, 256 448 V 64 Z" fill="#009900"/>
      <path d="M256 64 C362 64, 416 150, 416 220 C416 350, 332 410, 256 448 V 64 Z" fill="#BB0000"/>
      <path d="M256 120 L320 200 H280 V360 H232 V200 H192 L256 120 Z" fill="#FFFFFF"/>
    </svg>
    """
    
    # Professional header with custom icon
    st.markdown(f'<div style="text-align: center;">{icon_svg}</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">TALANTA AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Kenya\'s AI-Powered Workforce Intelligence Platform</p>', unsafe_allow_html=True)
    
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("API key not configured. Please add GOOGLE_API_KEY to your .env file.")
        st.stop()

    # Professional sidebar
    with st.sidebar:
        st.markdown('<div class="profile-section">', unsafe_allow_html=True)
        st.subheader("Your Profile")
        
        # Profile inputs
        education = st.selectbox(
            "Education Level", 
            ["High School", "Diploma", "Undergraduate", "Masters", "PhD", "Self-Taught"],
            help="Select your highest level of education"
        )
        
        skills = st.text_area(
            "Current Skills", 
            placeholder="e.g., Python, Sales, Customer Service",
            help="List your key professional skills"
        )
        
        interests = st.text_area(
            "Career Interests", 
            placeholder="e.g., Remote work, Tech, Agriculture",
            help="Describe your career goals and interests"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Resume upload section
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.subheader("Resume Analysis")
        uploaded_resume = st.file_uploader("Upload CV (PDF)", type="pdf", help="Upload your resume for personalized analysis")
        resume_text = ""
        if uploaded_resume:
            resume_text = extract_text_from_pdf(uploaded_resume)
            if resume_text:
                st.markdown('<div class="status-success">Resume loaded successfully</div>', unsafe_allow_html=True)
                st.session_state.resume_text = resume_text
            else:
                st.error("Could not read PDF. Please try another file.")
        
        # Get resume text from session state if available
        if hasattr(st.session_state, 'resume_text'):
            resume_text = st.session_state.resume_text
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("New Chat", type="primary"):
                if hasattr(st.session_state, 'messages'):
                    st.session_state.messages = []
                st.rerun()
        
        with col2:
            if st.button("Clear All", type="secondary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # Export chat feature
        st.markdown("---")
        if hasattr(st.session_state, 'messages') and st.session_state.messages:
            chat_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in st.session_state.messages])
            st.download_button(
                label="Download Advice",
                data=chat_text,
                file_name="Talanta_Career_Advice.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        # Disclaimer
        st.markdown("---")
        st.caption(
            "**Disclaimer:** Talanta AI is an automated assistant. "
            "Information provided is for guidance only. "
            "Always verify salary data and legal requirements independently."
        )

    # Enhanced system instruction
    system_instruction = (
        f"ROLE: You are Talanta AI, a distinctively Kenyan career coach and workforce expert. "
        f"Your goal is to provide practical, encouraging, and locally relevant advice.\n\n"
        
        f"USER CONTEXT:\n"
        f"- Education Level: {education}\n"
        f"- Current Skills: {skills}\n"
        f"- Interests: {interests}\n"
        f"- Resume Content: {resume_text if resume_text else 'Not provided'}\n\n"
        
        f"BEHAVIOR GUIDELINES:\n"
        f"1. LANGUAGE: Detect the language of the user's prompt (English or Swahili). "
        f"Reply in the same language. If Swahili, use natural, conversational Kenyan Swahili, not robotic translation.\n"
        
        f"2. LOCAL RELEVANCE: When recommending job platforms, mention Kenyan specific ones "
        f"(e.g., BrighterMonday, Fuzu, LinkedIn Kenya, Kuhustle). "
        f"Acknowledge the Kenyan market reality (e.g., the value of networking/'connections', the gig economy, remote work options).\n"
        
        f"3. TONE: Be a mentor. Be encouraging but realistic. "
        f"If the user has low education but high skills, emphasize their portfolio. "
        f"If the user has high education but no skills, emphasize internships and certifications.\n"
        
        f"4. FORMAT: Keep responses short (under 150 words). Use bullet points. "
        f"End with one specific 'Next Step' for the user to take immediately.\n"
        
        f"5. RESUME ANALYSIS: If resume content is provided, reference specific details "
        f"from their CV when giving advice. Point out strengths and identify gaps."
    )

    # Initialize chat with context preservation
    if "messages" not in st.session_state:
        st.session_state.messages = []
        initial_msg = "Habari! I am Talanta AI. I have reviewed your profile. How can I help you navigate your career today?"
        st.session_state.messages.append({"role": "assistant", "content": initial_msg})

    # Professional chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history without avatars
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=None):
            st.markdown(message["content"])

    # Quick action buttons for new users
    user_input = None
    if len(st.session_state.messages) <= 1:
        st.subheader("Quick Starts")
        col1, col2, col3 = st.columns(3)
        
        if col1.button("Review my Profile", use_container_width=True):
            user_input = "Please review my profile and CV. Tell me my top 3 strengths and 1 major area for improvement."
        
        if col2.button("Mock Interview", use_container_width=True):
            user_input = "I want to practice for a job interview. Act as the interviewer and ask me one question at a time."
        
        if col3.button("Salary Guide", use_container_width=True):
            user_input = "Based on my skills and education, what is the salary range for my role in Nairobi right now?"

    # Handle chat input
    if chat_input := st.chat_input("Ask about your career path or type in Swahili..."):
        user_input = chat_input

    # Unified processing logic
    if user_input:
        # Display user message
        with st.chat_message("user", avatar=None):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generate AI response with conversation context
        with st.chat_message("assistant", avatar=None):
            message_placeholder = st.empty()
            message_placeholder.markdown("Analyzing your query...")
            
            try:
                # Build full conversation context for consistency
                conversation_context = system_instruction + "\n\nConversation History:\n"
                
                # Include recent conversation for context (last 8 messages)
                recent_messages = st.session_state.messages[-8:]
                for msg in recent_messages:
                    conversation_context += f"{msg['role'].title()}: {msg['content']}\n"
                
                conversation_context += f"\nUser: {user_input}\nAssistant:"
                
                # Generate response with full context
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=conversation_context
                )
                
                response_text = response.text
                message_placeholder.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # Force rerun to update download button
                st.rerun()
                
            except Exception as e:
                error_msg = f"Service temporarily unavailable. Please try again."
                message_placeholder.error(error_msg)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main execution with mobile-responsive configuration
if __name__ == "__main__":
    st.set_page_config(
        page_title="TALANTA AI - Workforce Intelligence Platform",
        page_icon="T",
        layout="centered",
        initial_sidebar_state="auto"
    )
    career_advisor_tab()