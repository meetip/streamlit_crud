import streamlit as st
import json
import os
from typing import List, Dict

# Default Google Sheet ID (from user-provided link). If you prefer, set env var SHEET_ID to override.
SHEET_ID_DEFAULT = "1aBQwOqcUWyaL3TZ0dFBGUL4e4o7IJr2y_YipN_Z1jcI"

# Page config
st.set_page_config(page_title="MCQ Review App", layout="wide")

# Custom CSS for larger fonts and wider sidebar
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
    /* Wider sidebar to show full dropdown text */
    section[data-testid="stSidebar"] {
        width: 450px !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 450px !important;
    }
</style>
""", unsafe_allow_html=True)

# Load / Save data


def _load_from_json(path: str = "data.json") -> List[Dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def _save_to_json(data: List[Dict], path: str = "data.json") -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@st.cache_data
def load_data() -> List[Dict]:
    """Try to load data from Google Sheets if configured, otherwise fall back to local data.json.

    To use Google Sheets, set env vars `SHEET_ID` and `SERVICE_ACCOUNT_FILE` (path to JSON key).
    The sheet should have a header row with column names matching the JSON keys (e.g., Chapter, คำถาม, ตัวเลือก A, ...).
    """
    # Determine sheet_id and credentials source: env vars, Streamlit secrets, or default
    sheet_id = os.environ.get('SHEET_ID') or (
        st.secrets.get('SHEET_ID') if st.secrets else None)
    if not sheet_id:
        sheet_id = SHEET_ID_DEFAULT

    # Credentials: prefer Streamlit secrets (service account JSON as dict or string), then env file
    service_info = None
    if st.secrets and ('gcp_service_account' in st.secrets or 'SERVICE_ACCOUNT' in st.secrets or 'service_account' in st.secrets):
        # support both nested dict and raw JSON string
        for key in ('gcp_service_account', 'SERVICE_ACCOUNT', 'service_account'):
            if key in st.secrets:
                service_info = st.secrets[key]
                break

    service_file = os.environ.get('SERVICE_ACCOUNT_FILE')

    # If we have either a service file or service_info, try Sheets
    if (sheet_id) and (service_info or (service_file and os.path.exists(service_file))):
        try:
            import gspread
            try:
                # prefer in-memory info
                from google.oauth2.service_account import Credentials
            except Exception:
                Credentials = None

            scopes = ['https://www.googleapis.com/auth/spreadsheets']

            if service_info:
                # If service_info is a JSON string, parse it
                if isinstance(service_info, str):
                    try:
                        service_info = json.loads(service_info)
                    except Exception:
                        pass

                creds = Credentials.from_service_account_info(
                    service_info, scopes=scopes)
            else:
                creds = Credentials.from_service_account_file(
                    service_file, scopes=scopes)

            gc = gspread.authorize(creds)
            sh = gc.open_by_key(sheet_id)
            ws = sh.sheet1
            records = ws.get_all_records()

            # Normalize types: ensure Chapter is int where possible
            for r in records:
                if 'Chapter' in r:
                    try:
                        r['Chapter'] = int(r['Chapter'])
                    except Exception:
                        pass
                # Normalize empty strings to None for optional fields
                for k, v in list(r.items()):
                    if isinstance(v, str) and v.strip() == '':
                        r[k] = None

            return records
        except Exception as e:
            # If Sheets loading fails, fall back to JSON but show a warning
            st.warning(
                f"Could not load from Google Sheets: {e}. Falling back to data.json.")
            return _load_from_json()

    # Default fallback
    return _load_from_json()


def save_data(data: List[Dict]) -> None:
    """Save to Google Sheets if configured, else to `data.json`.

    WARNING: When saving to a Google Sheet this will overwrite the sheet contents.
    """
    # Resolve sheet id and credentials (support Streamlit Cloud secrets)
    sheet_id = os.environ.get('SHEET_ID') or (
        st.secrets.get('SHEET_ID') if st.secrets else None)
    if not sheet_id:
        sheet_id = SHEET_ID_DEFAULT

    service_info = None
    if st.secrets and ('gcp_service_account' in st.secrets or 'SERVICE_ACCOUNT' in st.secrets or 'service_account' in st.secrets):
        for key in ('gcp_service_account', 'SERVICE_ACCOUNT', 'service_account'):
            if key in st.secrets:
                service_info = st.secrets[key]
                break

    service_file = os.environ.get('SERVICE_ACCOUNT_FILE')

    if (sheet_id) and (service_info or (service_file and os.path.exists(service_file))):
        try:
            import gspread
            try:
                from google.oauth2.service_account import Credentials
            except Exception:
                Credentials = None

            scopes = ['https://www.googleapis.com/auth/spreadsheets']

            if service_info:
                if isinstance(service_info, str):
                    try:
                        service_info = json.loads(service_info)
                    except Exception:
                        pass
                creds = Credentials.from_service_account_info(
                    service_info, scopes=scopes)
            else:
                creds = Credentials.from_service_account_file(
                    service_file, scopes=scopes)

            gc = gspread.authorize(creds)
            sh = gc.open_by_key(sheet_id)
            ws = sh.sheet1

            # Build header from keys of first row (fallback to previous header)
            if not data:
                ws.clear()
                return

            # Determine all unique keys to use as columns (preserve order-ish)
            keys = []
            for item in data:
                for k in item.keys():
                    if k not in keys:
                        keys.append(k)

            # Prepare rows
            rows = [keys]
            for item in data:
                row = [item.get(k, '') if item.get(k, '')
                       is not None else '' for k in keys]
                rows.append(row)

            ws.clear()
            ws.update(rows)
            return
        except Exception as e:
            st.warning(
                f"Could not save to Google Sheets: {e}. Saving to data.json instead.")
            _save_to_json(data)
            return

    # Default fallback
    _save_to_json(data)

# Main app


def main():
    st.title("📚 MCQ Review Application")

    # Chapter names dictionary
    chapter_names = {
        1: "How Large-Scale AI Works (อ.เติ้ล)",
        2: "What AI Is Good At – And Why It Sometimes Fails (อ.โรเจอร์)",
        3: "Can We Trust AI to Be Fair? (อ.เติ้ล)",
        4: "How to Evaluate AI Outputs (อ.ม่วย)",
        5: "Trusting Information in the Age of AI (อ.ม่วย)",
        6: "Personalization: Algorithms That Learn What You Like (อ.ยุ้ย)",
        7: "AI for All: Accessibility and Inclusion (อ.เม้ง อ.ปิงปอง)",
        8: "Understanding AI and Emotion (อ.เม้ง อ.ปิงปอง)",
        9: "Case Studies: How Thai Educators Are Using AI (อ.แจว อ.โบ)",
        10: "The Future of Responsible AI for Everyone (อ.สิริวุฒิ)"
    }

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
        format_func=lambda x: f"Chapter {x}: {chapter_names.get(x, 'Unknown')}"
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
