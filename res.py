import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import tempfile

# Set Streamlit page configuration first
st.set_page_config(page_title="AI Resume Generator", page_icon="📝", layout="wide")

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Gemini API key not found. Please set it in the .env file.")
    st.stop()

# Configure Gemini API
genai.configure(api_key="AIzaSyCmoqnAdEuXy9mstE4RNwIVxDraRgtlxpU")

# Initialize session state for resume data
if "resume_data" not in st.session_state:
    st.session_state.resume_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "(123) 456-7890",
        "linkedin": "linkedin.com/in/johndoe",
        "skills": "Python, Data Analysis, Communication",
        "experience": "",
        "education": "",
        "job_description": "",
        "summary": "A highly motivated professional."
    }

# --- Helper Functions ---
def generate_resume_content(prompt_text):
    """Generate content using Gemini AI."""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')  # Updated to a valid model
        response = model.generate_content(prompt_text)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating content with Gemini AI: {e}")
        return None

def get_resume_template(template_choice, data):
    """Generate resume content based on selected template."""
    name = data.get("name", "Your Name")
    email = data.get("email", "your.email@example.com")
    phone = data.get("phone", "(123) 456-7890")
    linkedin = data.get("linkedin", "linkedin.com/in/yourprofile")
    summary = data.get("summary", "A highly motivated professional.")
    skills = data.get("skills", "Communication, Problem-solving, Teamwork")
    experience = data.get("experience", "No experience provided.")
    education = data.get("education", "No education provided.")

    templates = {
        "Professional": f"""
# {name}
{email} | {phone} | {linkedin}

## Professional Summary
{summary}

## Key Skills
{skills}

## Work Experience
{experience}

## Education
{education}
""",
        "Modern": f"""
**{name.upper()}**
*Email:* {email} | *Phone:* {phone} | *LinkedIn:* {linkedin}

---

## **PROFESSIONAL SUMMARY**
{summary}

---

## **SKILLS**
{skills}

---

## **WORK EXPERIENCE**
{experience}

---

## **EDUCATION**
{education}
""",
        "Simple": f"""
{name}
Contact: {email}, {phone}, {linkedin}

**Summary:**
{summary}

**Skills:**
{skills}

**Experience:**
{experience}

**Education:**
{education}
"""
    }
    return templates.get(template_choice, templates["Simple"])

def create_pdf(resume_content, image_path=None, filename="resume.pdf"):
    """Generate a styled PDF using ReportLab."""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        custom_style = ParagraphStyle(
            name='Custom',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            spaceAfter=8
        )
        title_style = ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12
        )
        story = []

        # Add profile picture if provided
        if image_path:
            try:
                img = ReportLabImage(image_path, width=1*inch, height=1*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                st.warning(f"Error adding image to PDF: {e}")

        # Add resume content
        for line in resume_content.split('\n'):
            if line.startswith('# '):
                story.append(Paragraph(line[2:], title_style))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], styles['Heading2']))
            else:
                story.append(Paragraph(line, custom_style))
            story.append(Spacer(1, 0.1*inch))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

# --- Streamlit Application ---
st.title("📝 AI-Powered Resume Generator")
st.markdown("Create a tailored resume with AI assistance. Fill in your details, select a template, and optionally tailor it to a job description.")

# Sidebar for input
with st.sidebar:
    st.header("Your Information")
    uploaded_image = st.file_uploader("Profile Picture (optional)", type=["png", "jpg", "jpeg"])
    st.session_state.resume_data["name"] = st.text_input("Full Name", st.session_state.resume_data["name"])
    st.session_state.resume_data["email"] = st.text_input("Email", st.session_state.resume_data["email"])
    st.session_state.resume_data["phone"] = st.text_input("Phone", st.session_state.resume_data["phone"])
    st.session_state.resume_data["linkedin"] = st.text_input("LinkedIn Profile (URL)", st.session_state.resume_data["linkedin"])

    st.markdown("---")
    st.header("Resume Content")
    st.session_state.resume_data["job_description"] = st.text_area("Job Description (for tailoring)", st.session_state.resume_data["job_description"], height=150, placeholder="Paste the job description here...")
    st.session_state.resume_data["skills"] = st.text_area("Skills (comma-separated)", st.session_state.resume_data["skills"], height=100)
    st.session_state.resume_data["experience"] = st.text_area("Experience (e.g., 'Company A, Role, Dates, Responsibilities')", st.session_state.resume_data["experience"], height=200)
    st.session_state.resume_data["education"] = st.text_area("Education (e.g., 'University, Degree, Dates')", st.session_state.resume_data["education"], height=100)

    st.markdown("---")
    st.header("Options")
    template_choice = st.selectbox("Resume Template", ["Professional", "Modern", "Simple"])
    ai_refinement_option = st.checkbox("Tailor Resume to Job Description", value=True)

# Main content
st.markdown("## Resume Preview")

# Generate/Update Resume
if st.sidebar.button("Generate Resume", key="generate"):
    with st.spinner("Generating resume..."):
        # Generate Summary
        summary_prompt = f"""
        Generate a concise professional summary (3-4 sentences) for a resume based on:
        Skills: {st.session_state.resume_data['skills']}
        Experience: {st.session_state.resume_data['experience']}
        Education: {st.session_state.resume_data['education']}
        Job Description: {st.session_state.resume_data['job_description'] if st.session_state.resume_data['job_description'] else 'N/A'}
        """
        generated_summary = generate_resume_content(summary_prompt)
        st.session_state.resume_data["summary"] = generated_summary if generated_summary else "Failed to generate summary."

        # AI Refinement
        if ai_refinement_option and st.session_state.resume_data["job_description"]:
            with st.spinner("Refining content with AI..."):
                # Refine Skills
                skills_prompt = f"""
                Refine the following skills to highlight those most relevant to the job description (comma-separated).
                Current Skills: {st.session_state.resume_data['skills']}
                Job Description: {st.session_state.resume_data['job_description']}
                """
                refined_skills = generate_resume_content(skills_prompt)
                if refined_skills:
                    st.session_state.resume_data["skills"] = refined_skills
                    st.info(f"Refined Skills: {refined_skills}")

                # Refine Experience
                experience_prompt = f"""
                Rephrase the experience to emphasize achievements relevant to the job description. Use bullet points.
                Current Experience: {st.session_state.resume_data['experience']}
                Job Description: {st.session_state.resume_data['job_description']}
                """
                refined_experience = generate_resume_content(experience_prompt)
                if refined_experience:
                    st.session_state.resume_data["experience"] = refined_experience
                    st.info(f"Refined Experience:\n{refined_experience}")

                # Refine Education
                education_prompt = f"""
                Highlight relevant coursework or projects from the education based on the job description.
                Current Education: {st.session_state.resume_data['education']}
                Job Description: {st.session_state.resume_data['job_description']}
                """
                refined_education = generate_resume_content(education_prompt)
                if refined_education:
                    st.session_state.resume_data["education"] = refined_education
                    st.info(f"Refined Education:\n{refined_education}")

    st.success("Resume generated successfully!")

# Display Resume
resume_content_markdown = get_resume_template(template_choice, st.session_state.resume_data)
if uploaded_image:
    try:
        image = Image.open(uploaded_image)
        st.image(image, caption="Profile Picture", width=150)
    except Exception as e:
        st.warning(f"Error displaying image: {e}")
st.markdown(resume_content_markdown)

# Download Options
st.markdown("---")
st.subheader("Download Resume")

col1, col2 = st.columns(2)
with col1:
    if st.button("Download as PDF", key="download_pdf"):
        image_path = None
        if uploaded_image:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    Image.open(uploaded_image).save(tmp.name)
                    image_path = tmp.name
                pdf_data = create_pdf(resume_content_markdown, image_path)
                if pdf_data:
                    st.download_button(
                        label="Download PDF",
                        data=pdf_data,
                        file_name="resume.pdf",
                        mime="application/pdf",
                        key="download_pdf_button"
                    )
                if image_path and os.path.exists(image_path):
                    os.unlink(image_path)
            except Exception as e:
                st.error(f"Error processing image for PDF: {e}")
        else:
            pdf_data = create_pdf(resume_content_markdown)
            if pdf_data:
                st.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name="resume.pdf",
                    mime="application/pdf",
                    key="download_pdf_button"
                )

with col2:
    st.download_button(
        label="Download as Text",
        data=resume_content_markdown.encode('utf-8'),
        file_name="resume.txt",
        mime="text/plain",
        key="download_txt"
    )

# Tips
st.markdown("---")
st.info("""
**Tips for Best Results:**
- Provide a detailed job description for accurate AI tailoring.
- Use clear, concise inputs for skills, experience, and education.
- Preview the resume before downloading to ensure accuracy.
- For advanced PDF styling, the app uses ReportLab for professional formatting.
- Ensure the GEMINI_API_KEY is set in a `.env` file for secure API access.
""")
