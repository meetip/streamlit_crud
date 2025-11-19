import streamlit as st
import json
from typing import List, Dict

# Page config
st.set_page_config(page_title="MCQ Review App", layout="wide")

# Custom CSS for larger fonts
st.markdown("""
<style>
    .stMarkdown, .stText {
        font-size: 1.2rem;
    }
    h1 {
        font-size: 2.5rem !important;
    }
    h2 {
        font-size: 2rem !important;
    }
    h3 {
        font-size: 1.5rem !important;
    }
    .stTextArea textarea, .stTextInput input {
        font-size: 1.1rem;
    }
    div[data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Load data


@st.cache_data
def load_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("data.json not found!")
        return []

# Save data


def save_data(data: List[Dict]):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Main app


def main():
    st.title("📚 MCQ Review Application")

    # Load questions
    questions = load_data()

    if not questions:
        st.warning("No questions found in data.json")
        return

    # Get unique chapters
    chapters = sorted(list(set([q['Chapter'] for q in questions])))

    # Sidebar - Chapter selection
    st.sidebar.header("🔖 Select Chapter")
    selected_chapter = st.sidebar.selectbox(
        "Choose a chapter:",
        chapters,
        format_func=lambda x: f"Chapter {x}"
    )

    # Filter questions by chapter
    chapter_questions = [
        q for q in questions if q['Chapter'] == selected_chapter]

    # Show chapter info
    total_questions = len(chapter_questions)
    checked_questions = len(
        [q for q in chapter_questions if q.get('status') == 'checked'])

    st.sidebar.metric("Total Questions", total_questions)
    st.sidebar.metric("Checked", checked_questions)
    st.sidebar.metric("Remaining", total_questions - checked_questions)

    # Progress bar
    if total_questions > 0:
        progress = checked_questions / total_questions
        st.sidebar.progress(progress)
        st.sidebar.caption(f"{int(progress * 100)}% Complete")

    # Summary table for all chapters
    st.sidebar.divider()
    st.sidebar.subheader("📊 All Chapters Summary")

    summary_data = []
    for ch in chapters:
        ch_questions = [q for q in questions if q['Chapter'] == ch]
        ch_total = len(ch_questions)
        ch_checked = len(
            [q for q in ch_questions if q.get('status') == 'checked'])
        summary_data.append({
            "Chapter": ch,
            "Questions": ch_total,
            "Checked": ch_checked
        })

    # Display as table
    import pandas as pd
    df = pd.DataFrame(summary_data)
    st.sidebar.dataframe(df, hide_index=True, use_container_width=True)

    # Main content area
    st.header(f"Chapter {selected_chapter}")

    # Question navigation
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0

    # Ensure index is within bounds
    if st.session_state.current_index >= len(chapter_questions):
        st.session_state.current_index = 0

    if chapter_questions:
        current_q = chapter_questions[st.session_state.current_index]
        original_index = questions.index(current_q)

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Previous") and st.session_state.current_index > 0:
                st.session_state.current_index -= 1
                st.rerun()
        with col2:
            st.write(
                f"Question {st.session_state.current_index + 1} of {total_questions}")
        with col3:
            if st.button("Next ➡️") and st.session_state.current_index < total_questions - 1:
                st.session_state.current_index += 1
                st.rerun()

        st.divider()

        # Show status
        status = current_q.get('status', 'unchecked')
        if status == 'checked':
            st.success("✅ This question has been checked")
        else:
            st.info("⏳ This question needs review")

        # Edit mode toggle
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False

        edit_col1, edit_col2 = st.columns([1, 4])
        with edit_col1:
            if st.button("✏️ Edit" if not st.session_state.edit_mode else "👁️ View"):
                st.session_state.edit_mode = not st.session_state.edit_mode
                st.rerun()

        st.divider()

        # Display/Edit question
        if st.session_state.edit_mode:
            # Edit mode
            with st.form(key=f"edit_form_{original_index}"):
                st.subheader("Edit Question")

                หัวข้อ = st.text_area(
                    "หัวข้อ:", value=current_q.get('หัวข้อ', ''), height=100)
                คำถาม = st.text_area(
                    "คำถาม:", value=current_q.get('คำถาม', ''), height=100)

                col_a, col_b = st.columns(2)
                with col_a:
                    ตัวเลือก_A = st.text_area(
                        "ตัวเลือก A:", value=current_q.get('ตัวเลือก A', ''), height=80)
                    ตัวเลือก_C = st.text_area(
                        "ตัวเลือก C:", value=current_q.get('ตัวเลือก C', ''), height=80)
                with col_b:
                    ตัวเลือก_B = st.text_area(
                        "ตัวเลือก B:", value=current_q.get('ตัวเลือก B', ''), height=80)
                    ตัวเลือก_D = st.text_area(
                        "ตัวเลือก D:", value=current_q.get('ตัวเลือก D', ''), height=80)

                คำตอบที่ถูก = st.selectbox("คำตอบที่ถูก:", ['A', 'B', 'C', 'D'],
                                           index=['A', 'B', 'C', 'D'].index(current_q.get('คำตอบที่ถูก', 'A')))

                คำอธิบาย = st.text_area(
                    "คำอธิบาย:", value=current_q.get('คำอธิบาย', ''), height=100)

                หมายเหตุการรวม = st.text_input(
                    "หมายเหตุการรวม:", value=current_q.get('หมายเหตุการรวม', '') or '')

                submit_col1, submit_col2 = st.columns(2)
                with submit_col1:
                    save_button = st.form_submit_button(
                        "💾 Save Changes", use_container_width=True)
                with submit_col2:
                    cancel_button = st.form_submit_button(
                        "❌ Cancel", use_container_width=True)

                if save_button:
                    # Update the question
                    questions[original_index]['หัวข้อ'] = หัวข้อ
                    questions[original_index]['คำถาม'] = คำถาม
                    questions[original_index]['ตัวเลือก A'] = ตัวเลือก_A
                    questions[original_index]['ตัวเลือก B'] = ตัวเลือก_B
                    questions[original_index]['ตัวเลือก C'] = ตัวเลือก_C
                    questions[original_index]['ตัวเลือก D'] = ตัวเลือก_D
                    questions[original_index]['คำตอบที่ถูก'] = คำตอบที่ถูก
                    questions[original_index]['คำอธิบาย'] = คำอธิบาย
                    questions[original_index]['หมายเหตุการรวม'] = หมายเหตุการรวม if หมายเหตุการรวม else None

                    save_data(questions)
                    st.success("✅ Changes saved successfully!")
                    st.session_state.edit_mode = False
                    st.cache_data.clear()
                    st.rerun()

                if cancel_button:
                    st.session_state.edit_mode = False
                    st.rerun()

        else:
            # View mode
            st.subheader("📖 Review Question")

            st.markdown(f"**คำถาม:** {current_q.get('คำถาม', 'N/A')}")

            st.markdown("**ตัวเลือก:**")
            for option in ['A', 'B', 'C', 'D']:
                option_text = current_q.get(f'ตัวเลือก {option}', 'N/A')
                is_correct = current_q.get('คำตอบที่ถูก', '') == option
                if is_correct:
                    st.markdown(f"✅ **{option}.** {option_text}")
                else:
                    st.markdown(f"   {option}. {option_text}")

            st.markdown(f"**คำอธิบาย:** {current_q.get('คำอธิบาย', 'N/A')}")

            st.divider()

            # Confirm button
            if status != 'checked':
                if st.button("✅ Confirm & Mark as Checked", use_container_width=True, type="primary"):
                    questions[original_index]['status'] = 'checked'
                    save_data(questions)
                    st.success("Question marked as checked!")
                    st.cache_data.clear()
                    st.rerun()
            else:
                if st.button("↩️ Uncheck this question", use_container_width=True):
                    questions[original_index]['status'] = 'unchecked'
                    save_data(questions)
                    st.info("Question unmarked")
                    st.cache_data.clear()
                    st.rerun()


if __name__ == "__main__":
    main()
