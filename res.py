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

# Load environment variables
load_dotenv()

# Configure Gemini API
API_KEY = "AIzaSyD7fSCEABwq3JezjAVh8ujVGYlps_iuXi4"
if not API_KEY:
    st.error("GEMINI_API_KEY not found in .env file. Please set it.")
    st.stop()
genai.configure(api_key=API_KEY)

# --- Helper Functions ---
def generate_resume_content(prompt_text):
    """Generate content using Gemini AI."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')  # Updated to a valid model
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
        img = ReportLabImage(image_path, width=1*inch, height=1*inch)
        story.append(img)
        story.append(Spacer(1, 0.2*inch))

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

# --- Streamlit Application ---
st.set_page_config(page_title="AI Resume Generator", page_icon="📝", layout="wide")

st.title("📝 AI-Powered Resume Generator")
st.markdown("Create a tailored resume with AI assistance. Fill in your details, select a template, and optionally tailor it to a job description.")

# Sidebar for input
with st.sidebar:
    st.header("Your Information")
    uploaded_image = st.file_uploader("Profile Picture (optional)", type=["png", "jpg", "jpeg"])
    name = st.text_input("Full Name", "John Doe")
    email = st.text_input("Email", "john.doe@example.com")
    phone = st.text_input("Phone", "(123) 456-7890")
    linkedin = st.text_input("LinkedIn Profile (URL)", "linkedin.com/in/johndoe")

    st.markdown("---")
    st.header("Resume Content")
    job_description_input = st.text_area("Job Description (for tailoring)", height=150, placeholder="Paste the job description here...")
    skills_input = st.text_area("Skills (comma-separated)", "Python, Data Analysis, Communication")
    experience_input = st.text_area("Experience (e.g., 'Company A, Role, Dates, Responsibilities')", height=200)
    education_input = st.text_area("Education (e.g., 'University, Degree, Dates')", height=100)

    st.markdown("---")
    st.header("Options")
    template_choice = st.selectbox("Resume Template", ["Professional", "Modern", "Simple"])
    ai_refinement_option = st.checkbox("Tailor Resume to Job Description", value=True)

# Main content
st.markdown("## Resume Preview")

# Store resume data
resume_data = {
    "name": name,
    "email": email,
    "phone": phone,
    "linkedin": linkedin,
    "skills": skills_input,
    "experience": experience_input,
    "education": education_input,
    "job_description": job_description_input
}

# Generate/Update Resume
if st.sidebar.button("Generate Resume", key="generate"):
    with st.spinner("Generating resume..."):
        # Generate Summary
        summary_prompt = f"""
        Generate a concise professional summary (3-4 sentences) for a resume based on:
        Skills: {skills_input}
        Experience: {experience_input}
        Education: {education_input}
        Job Description: {job_description_input if job_description_input else 'N/A'}
        """
        generated_summary = generate_resume_content(summary_prompt)
        resume_data["summary"] = generated_summary if generated_summary else "Failed to generate summary."

        # AI Refinement
        if ai_refinement_option and job_description_input:
            with st.spinner("Refining content with AI..."):
                # Refine Skills
                skills_prompt = f"""
                Refine the following skills to highlight those most relevant to the job description (comma-separated).
                Current Skills: {skills_input}
                Job Description: {job_description_input}
                """
                refined_skills = generate_resume_content(skills_prompt)
                if refined_skills:
                    resume_data["skills"] = refined_skills
                    st.info(f"Refined Skills: {refined_skills}")

                # Refine Experience
                experience_prompt = f"""
                Rephrase the experience to emphasize achievements relevant to the job description. Use bullet points.
                Current Experience: {experience_input}
                Job Description: {job_description_input}
                """
                refined_experience = generate_resume_content(experience_prompt)
                if refined_experience:
                    resume_data["experience"] = refined_experience
                    st.info(f"Refined Experience:\n{refined_experience}")

                # Refine Education
                education_prompt = f"""
                Highlight relevant coursework or projects from the education based on the job description.
                Current Education: {education_input}
                Job Description: {job_description_input}
                """
                refined_education = generate_resume_content(education_prompt)
                if refined_education:
                    resume_data["education"] = refined_education
                    st.info(f"Refined Education:\n{refined_education}")

    st.success("Resume generated successfully!")

# Display Resume
resume_content_markdown = get_resume_template(template_choice, resume_data)
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="Profile Picture", width=150)
st.markdown(resume_content_markdown)

# Download Options
st.markdown("---")
st.subheader("Download Resume")

col1, col2 = st.columns(2)
with col1:
    if st.button("Download as PDF", key="download_pdf"):
        image_path = None
        if uploaded_image:
            image_path = "temp_image.png"
            Image.open(uploaded_image).save(image_path)
        pdf_data = create_pdf(resume_content_markdown, image_path)
        st.download_button(
            label="Download PDF",
            data=pdf_data,
            file_name="resume.pdf",
            mime="application/pdf",
            key="download_pdf_button"
        )
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

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
""")
