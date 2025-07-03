import streamlit as st
from agent import appointment_agent
from langchain_core.messages import HumanMessage

def main():
    st.set_page_config(page_title="Appointment Scheduler", layout="wide")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    st.title("📅 Calendar Booking Assistant")
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("How can I help schedule your appointment?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        try:
            result = appointment_agent.invoke({
                "messages": [HumanMessage(content=prompt)],
                "user_intent": "",
                "appointment_details": {}
            })
            response = result["messages"][-1].content
        except Exception as e:
            response = f"🔴 System error: {str(e)}"
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main()