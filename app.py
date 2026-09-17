import io
import json
import re
import random
import streamlit as st
from pypdf import PdfReader

st.set_page_config(
    page_title="AI Study & Question Paper Generator",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Study & Question Paper Generator")
st.write(
    "Upload a textbook PDF, select a chapter/unit, and generate MCQs, "
    "short questions, long questions, or a complete question paper."
)


# -----------------------------
# PDF FUNCTIONS
# -----------------------------
def extract_pdf_pages(uploaded_file):
    reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({
            "page": page_number,
            "text": text
        })

    return pages


def detect_chapters(pages):
    """
    Detect common headings such as:
    Chapter 1
    CHAPTER 2: Computer System
    Unit 3
    UNIT 5 - Applications of Computer
    """

    chapter_pattern = re.compile(
        r"^\s*(chapter|unit)\s*"
        r"([0-9]+|[IVXLC]+)"
        r"\s*[\-:.\)]?\s*(.*)$",
        re.IGNORECASE
    )

    sections = {}
    current_section = "Full Book"
    sections[current_section] = []

    for page in pages:
        lines = page["text"].splitlines()

        detected = None

        for line in lines[:25]:
            clean_line = re.sub(r"\s+", " ", line).strip()

            if not clean_line:
                continue

            match = chapter_pattern.match(clean_line)

            if match:
                detected = clean_line
                break

        if detected:
            current_section = detected

            if current_section not in sections:
                sections[current_section] = []

        sections[current_section].append(page)

    return sections


def get_text(pages, max_chars=50000):
    text_parts = []

    for page in pages:
        text_parts.append(
            f"\n[Page {page['page']}]\n{page['text']}"
        )

    return "\n".join(text_parts)[:max_chars]


# -----------------------------
# AI GENERATION
# -----------------------------
def generate_questions_ai(
    context,
    question_type,
    number,
    marks,
    difficulty,
    api_key,
    model
):
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    if question_type == "MCQs":
        structure = """
        Each item must contain:
        question
        options: exactly four options
        answer
        explanation
        """

    else:
        structure = """
        Each item must contain:
        question
        options: []
        answer
        explanation
        """

    prompt = f"""
You are an experienced secondary-school Computer Science teacher.

Generate {number} {question_type} from ONLY the textbook content provided below.

Chapter/Unit content:
{context}

Requirements:
1. Do not use information outside the supplied textbook.
2. Do not invent facts.
3. Avoid duplicate questions.
4. Difficulty level: {difficulty}.
5. Each question carries {marks} marks.
6. Use clear language suitable for school students.
7. For MCQs, provide exactly four options.
8. For MCQs, identify the correct answer.
9. For short questions, make questions appropriate for short written answers.
10. For long questions, make questions suitable for detailed answers.
11. Return valid JSON only.

Return:
{{
    "items": [
        {{
            "question": "...",
            "options": [],
            "answer": "...",
            "explanation": "..."
        }}
    ]
}}

{structure}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    return result.get("items", [])


# -----------------------------
# OFFLINE FALLBACK
# -----------------------------
def fallback_generator(context, question_type, number):
    sentences = re.split(r"(?<=[.!?])\s+", context)

    sentences = [
        s.strip()
        for s in sentences
        if len(s.strip()) >= 40
    ]

    random.shuffle(sentences)

    if not sentences:
        return [{
            "question": "No sufficient readable text was found in this section.",
            "options": [],
            "answer": "",
            "explanation": ""
        }]

    items = []

    for sentence in sentences[:number]:

        if question_type == "MCQs":
            item = {
                "question": "Which statement is supported by the selected textbook section?",
                "options": [
                    sentence,
                    "The textbook does not discuss this topic.",
                    "This statement is unrelated to the selected chapter.",
                    "None of the above."
                ],
                "answer": sentence,
                "explanation": "The correct option is based on the extracted textbook text."
            }

        elif question_type == "Short Questions":
            item = {
                "question": f"Explain the following concept from the textbook: {sentence}",
                "options": [],
                "answer": "",
                "explanation": ""
            }

        else:
            item = {
                "question": f"Discuss the following concept in detail: {sentence}",
                "options": [],
                "answer": "",
                "explanation": ""
            }

        items.append(item)

    return items


# -----------------------------
# PAPER CREATION
# -----------------------------
def create_question_paper(
    chapter,
    mcqs,
    short_questions,
    long_questions,
    school_name,
    subject,
    class_name,
    session,
    total_marks,
    time_allowed
):
    lines = []

    lines.append(school_name)
    lines.append("=" * 70)
    lines.append("QUESTION PAPER")
    lines.append("=" * 70)
    lines.append(f"Academic Session: {session}")
    lines.append(f"Class: {class_name}")
    lines.append(f"Subject: {subject}")
    lines.append(f"Chapter / Unit: {chapter}")
    lines.append(f"Time Allowed: {time_allowed}")
    lines.append(f"Total Marks: {total_marks}")
    lines.append("")
    lines.append("Name: ______________________________")
    lines.append("Roll No: ____________________________")
    lines.append("")
    lines.append("-" * 70)

    number = 1

    if mcqs:
        lines.append("SECTION A — MULTIPLE CHOICE QUESTIONS")
        lines.append("")

        for item in mcqs:
            lines.append(f"{number}. {item['question']}")

            for option in item.get("options", []):
                lines.append(f"   {option}")

            lines.append("")
            number += 1

    if short_questions:
        lines.append("SECTION B — SHORT QUESTIONS")
        lines.append("")

        for item in short_questions:
            lines.append(f"{number}. {item['question']}")
            lines.append("")
            number += 1

    if long_questions:
        lines.append("SECTION C — LONG QUESTIONS")
        lines.append("")

        for item in long_questions:
            lines.append(f"{number}. {item['question']}")
            lines.append("")
            number += 1

    return "\n".join(lines)


# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.header("⚙️ Application Settings")

    school_name = st.text_input(
        "School / College Name",
        "Your School Name"
    )

    class_name = st.text_input(
        "Class",
        "Grade 11"
    )

    subject = st.text_input(
        "Subject",
        "Computer Science"
    )

    session = st.text_input(
        "Academic Session",
        "2026-27"
    )

    time_allowed = st.text_input(
        "Time Allowed",
        "2 Hours"
    )

    st.divider()

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="For deployed applications, preferably store this in Streamlit Secrets."
    )

    model = st.selectbox(
        "AI Model",
        [
            "gpt-4o-mini",
            "gpt-4o"
        ]
    )

    difficulty = st.selectbox(
        "Difficulty",
        [
            "Easy",
            "Medium",
            "Hard"
        ]
    )


# -----------------------------
# PDF UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "📖 Upload your textbook PDF",
    type=["pdf"]
)

if not uploaded_file:

    st.info(
        "Upload a PDF textbook to begin. "
        "For best results, use a text-based PDF rather than a scanned image-only PDF."
    )

    st.markdown("""
### Application workflow

1. Upload textbook PDF
2. Detect chapters/units
3. Select a chapter
4. Generate MCQs
5. Generate short questions
6. Generate long questions
7. Create complete question paper
8. Download the paper
""")

    st.stop()


# -----------------------------
# READ PDF
# -----------------------------
with st.spinner("Reading textbook PDF..."):
    pages = extract_pdf_pages(uploaded_file)
    chapters = detect_chapters(pages)

st.success(
    f"PDF loaded successfully — {len(pages)} pages detected."
)


# -----------------------------
# CHAPTER SELECTION
# -----------------------------
chapter_names = list(chapters.keys())

selected_chapter = st.selectbox(
    "📚 Select Chapter / Unit",
    chapter_names
)

selected_pages = chapters[selected_chapter]

context = get_text(selected_pages)

st.write(
    f"**Selected:** {selected_chapter}  |  "
    f"Pages: {len(selected_pages)}  |  "
    f"Extracted characters: {len(context):,}"
)


# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3 = st.tabs(
    [
        "📝 Generate Questions",
        "📄 Question Paper",
        "📖 Text Preview"
    ]
)


# -----------------------------
# TAB 1
# -----------------------------
with tab1:

    st.subheader("Generate Questions")

    question_type = st.selectbox(
        "Question Type",
        [
            "MCQs",
            "Short Questions",
            "Long Questions"
        ]
    )

    number = st.number_input(
        "Number of Questions",
        min_value=1,
        max_value=50,
        value=10
    )

    if question_type == "MCQs":
        marks = st.number_input(
            "Marks per MCQ",
            min_value=1,
            max_value=5,
            value=1
        )
    elif question_type == "Short Questions":
        marks = st.number_input(
            "Marks per Short Question",
            min_value=1,
            max_value=10,
            value=3
        )
    else:
        marks = st.number_input(
            "Marks per Long Question",
            min_value=2,
            max_value=20,
            value=6
        )

    if st.button(
        "🚀 Generate Questions",
        type="primary"
    ):

        with st.spinner("Generating questions..."):

            if api_key:

                try:
                    generated = generate_questions_ai(
                        context=context,
                        question_type=question_type,
                        number=int(number),
                        marks=int(marks),
                        difficulty=difficulty,
                        api_key=api_key,
                        model=model
                    )

                    generation_method = "AI"

                except Exception as error:

                    st.warning(
                        f"AI generation failed. Offline fallback used. Error: {error}"
                    )

                    generated = fallback_generator(
                        context,
                        question_type,
                        int(number)
                    )

                    generation_method = "Fallback"

            else:

                generated = fallback_generator(
                    context,
                    question_type,
                    int(number)
                )

                generation_method = "Offline fallback"

        st.session_state["generated_questions"] = generated
        st.session_state["generated_type"] = question_type

        st.success(
            f"{len(generated)} questions generated using {generation_method}."
        )


    if "generated_questions" in st.session_state:

        st.divider()

        for index, item in enumerate(
            st.session_state["generated_questions"],
            start=1
        ):

            st.markdown(
                f"### {index}. {item['question']}"
            )

            if item.get("options"):

                for option in item["options"]:
                    st.write(f"**{option}**")

            if st.checkbox(
                "Show answer",
                key=f"answer_{index}"
            ):

                if item.get("answer"):
                    st.success(item["answer"])

                if item.get("explanation"):
                    st.caption(item["explanation"])


# -----------------------------
# TAB 2 — PAPER
# -----------------------------
with tab2:

    st.subheader("📄 Complete Question Paper")

    col1, col2 = st.columns(2)

    with col1:
        paper_total_marks = st.number_input(
            "Total Marks",
            min_value=10,
            max_value=200,
            value=50,
            step=5
        )

        paper_mcqs = st.number_input(
            "Number of MCQs",
            min_value=0,
            max_value=50,
            value=10
        )

    with col2:

        paper_short = st.number_input(
            "Number of Short Questions",
            min_value=0,
            max_value=30,
            value=5
        )

        paper_long = st.number_input(
            "Number of Long Questions",
            min_value=0,
            max_value=20,
            value=3
        )

    st.caption(
        "Note: Set the numbers and marks according to your school's examination pattern."
    )

    if st.button(
        "📄 Generate Complete Question Paper",
        type="primary"
    ):

        all_mcqs = []
        all_short = []
        all_long = []

        with st.spinner("Generating complete paper..."):

            if api_key:

                try:

                    if paper_mcqs:
                        all_mcqs = generate_questions_ai(
                            context,
                            "MCQs",
                            int(paper_mcqs),
                            1,
                            difficulty,
                            api_key,
                            model
                        )

                    if paper_short:
                        all_short = generate_questions_ai(
                            context,
                            "Short Questions",
                            int(paper_short),
                            3,
                            difficulty,
                            api_key,
                            model
                        )

                    if paper_long:
                        all_long = generate_questions_ai(
                            context,
                            "Long Questions",
                            int(paper_long),
                            6,
                            difficulty,
                            api_key,
                            model
                        )

                except Exception as error:

                    st.warning(
                        f"AI generation error: {error}. Using fallback."
                    )

                    all_mcqs = fallback_generator(
                        context,
                        "MCQs",
                        int(paper_mcqs)
                    )

                    all_short = fallback_generator(
                        context,
                        "Short Questions",
                        int(paper_short)
                    )

                    all_long = fallback_generator(
                        context,
                        "Long Questions",
                        int(paper_long)
                    )

            else:

                all_mcqs = fallback_generator(
                    context,
                    "MCQs",
                    int(paper_mcqs)
                )

                all_short = fallback_generator(
                    context,
                    "Short Questions",
                    int(paper_short)
                )

                all_long = fallback_generator(
                    context,
                    "Long Questions",
                    int(paper_long)
                )

        paper = create_question_paper(
            chapter=selected_chapter,
            mcqs=all_mcqs,
            short_questions=all_short,
            long_questions=all_long,
            school_name=school_name,
            subject=subject,
            class_name=class_name,
            session=session,
            total_marks=int(paper_total_marks),
            time_allowed=time_allowed
        )

        st.session_state["paper"] = paper

    if "paper" in st.session_state:

        st.text_area(
            "Question Paper Preview",
            st.session_state["paper"],
            height=600
        )

        st.download_button(
            "⬇️ Download Question Paper (.txt)",
            data=st.session_state["paper"],
            file_name="question_paper.txt",
            mime="text/plain"
        )


# -----------------------------
# TAB 3 — PREVIEW
# -----------------------------
with tab3:

    st.subheader("📖 Selected Chapter Text")

    st.text_area(
        "Extracted textbook content",
        context,
        height=600
    )
