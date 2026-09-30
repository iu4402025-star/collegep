import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="Student Study Roadmap",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Student Study Roadmap Generator")
st.write("Create a personalized step-by-step study roadmap with AI.")

# Get API key securely from Streamlit Secrets
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    api_key = ""

with st.sidebar:
    st.header("📚 Study Settings")
    subject = st.text_input("Subject", "Computer Science")
    topic = st.text_input("Topic / Chapter", "Python Programming")
    level = st.selectbox(
        "Student Level",
        ["Beginner", "Intermediate", "Advanced"]
    )
    days = st.slider("Study duration (days)", 1, 60, 7)
    hours = st.slider("Study hours per day", 1, 8, 2)

    generate = st.button("🚀 Generate Roadmap", use_container_width=True)

def generate_roadmap(subject, topic, level, days, hours):
    client = Groq(api_key=api_key)

    prompt = f"""
You are an expert educational planner.

Create a practical study roadmap for a student.

Subject: {subject}
Topic/Chapter: {topic}
Student level: {level}
Duration: {days} days
Study time per day: {hours} hours

Return a clear roadmap with:
1. Learning goals
2. Day-by-day plan
3. Topics/subtopics for each day
4. Practice activities
5. Revision tasks
6. A small self-test at the end
7. Tips for improving weak areas

Make the plan realistic for the available study time.
Use simple language suitable for students.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful educational study planner."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5,
        max_tokens=4000
    )

    return response.choices[0].message.content

if generate:
    if not api_key:
        st.error(
            "GROQ_API_KEY is missing. Add it in Streamlit Secrets "
            "or create .streamlit/secrets.toml for local testing."
        )
    else:
        with st.spinner("Creating your study roadmap..."):
            try:
                roadmap = generate_roadmap(
                    subject, topic, level, days, hours
                )
                st.success("Your roadmap is ready!")
                st.markdown(roadmap)
            except Exception as e:
                st.error(f"AI generation failed: {e}")

st.divider()
st.caption("AI-generated study plans should be reviewed and adjusted to match your course and exam requirements.")
