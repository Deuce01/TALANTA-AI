import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def career_advisor_tab():
    st.header("🇰🇪 Talanta AI: Career Advisor")
    st.write("Your personal workforce expert. Ask me anything in English or Swahili.")

    # --- Sidebar: User Profile ---
    with st.sidebar:
        st.header("👤 Your Profile")
        
        # API Key Input
        api_key = st.text_input("Enter Gemini API Key", type="password", value=os.getenv("GOOGLE_API_KEY", ""))
        if api_key:
            genai.configure(api_key=api_key)
        
        st.markdown("---")
        
        # Profile Inputs
        education = st.selectbox(
            "Education Level", 
            ["High School", "Diploma", "Undergraduate", "Masters", "PhD", "Self-Taught"]
        )
        
        skills = st.text_area(
            "Current Skills", 
            placeholder="E.g., Python, Graphic Design, Customer Service..."
        )
        
        interests = st.text_area(
            "Career Interests", 
            placeholder="E.g., Remote work, Agriculture, Tech startups..."
        )
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

    # --- Initialize Chat History ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Chat Logic & API Call ---
    if prompt := st.chat_input("Ask about your career path... / Uliza kuhusu kazi yako..."):
        
        # Check if API Key is present
        if not api_key:
            st.error("Please enter a Google Gemini API Key in the sidebar to continue.")
            return

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking... / Natafakari...")
            
            try:
                # System Instruction with user context
                system_instruction = (
                    f"You are Talanta AI, a Kenyan workforce expert. "
                    f"Answer in the user's language (English or Swahili). "
                    f"Use the user's profile context to tailor advice. "
                    f"User Profile -> Education: {education}, Skills: {skills}, Interests: {interests}. "
                    f"Keep answers concise and encouraging."
                )

                # Initialize Model and generate response
                model = genai.GenerativeModel('gemini-1.5-flash')
                full_prompt = f"{system_instruction}\n\nUser Question: {prompt}"
                response = model.generate_content(full_prompt)
                response_text = response.text

                # Display and store response
                message_placeholder.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

            except Exception as e:
                message_placeholder.error(f"An error occurred: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    st.set_page_config(page_title="Talanta AI", page_icon="🇰🇪")
    career_advisor_tab()