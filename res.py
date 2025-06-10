import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PIL import Image
from fpdf import FPDF # For basic PDF generation

# Load environment variables
load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("GEMINI_API_KEY not found in .env file. Please create one.")
    st.stop()
genai.configure(api_key=API_KEY)

# --- Helper function for Gemini AI generation ---
def generate_resume_content(prompt_text):
    try:
        model = genai.GenerativeModel('gemini-pro') # Using gemini-pro for text generation
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        st.error(f"Error generating content with Gemini AI: {e}")
        return None

# --- Resume Template Options ---
def get_resume_template(template_choice, data):
    """
    Generates resume content based on selected template and provided data.
    This is where you'd define different template structures.
    For now, it's a simple text-based template.
    """
    name = data.get("name", "Your Name")
    email = data.get("email", "your.email@example.com")
    phone = data.get("phone", "(123) 456-7890")
    linkedin = data.get("linkedin", "linkedin.com/in/yourprofile")
    summary = data.get("summary", "A highly motivated and results-oriented professional.")
    skills = data.get("skills", "Communication, Problem-solving, Teamwork")
    experience = data.get("experience", "No experience provided.")
    education = data.get("education", "No education provided.")
    job_description = data.get("job_description", "No job description provided (for tailoring).")

    if template_choice == "Professional":
        return f"""
# {name}
{email} | {phone} | {linkedin}

## Summary
{summary}

## Skills
{skills}

## Experience
{experience}

## Education
{education}
"""
    elif template_choice == "Modern":
        return f"""
**{name.upper()}**
*Email:* {email} | *Phone:* {phone} | *LinkedIn:* {linkedin}

---

## **ABOUT ME**
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
"""
    # Add more templates here
    else: # Default or custom template (can be expanded)
        return f"""
**{name}**
*Contact:* {email}, {phone}, {linkedin}

**Summary:**
{summary}

**Skills:**
{skills}

**Experience:**
{experience}

**Education:**
{education}
"""

# --- Streamlit Application ---
st.set_page_config(page_title="AI Resume Generator", page_icon="📝", layout="wide")

st.title("📝 AI-Powered Resume Generator")
st.markdown("---")

st.sidebar.header("Your Information")
uploaded_image = st.sidebar.file_uploader("Upload your profile picture (optional)", type=["png", "jpg", "jpeg"])
name = st.sidebar.text_input("Full Name", "John Doe")
email = st.sidebar.text_input("Email", "john.doe@example.com")
phone = st.sidebar.text_input("Phone", "(123) 456-7890")
linkedin = st.sidebar.text_input("LinkedIn Profile (URL)", "linkedin.com/in/johndoe")
st.sidebar.markdown("---")

st.sidebar.header("Resume Content")
job_description_input = st.sidebar.text_area("Job Description (for tailoring)", height=150,
                                         placeholder="Paste the job description here for AI to tailor your resume.")
skills_input = st.sidebar.text_area("Your Skills (comma-separated)", "Python, Data Analysis, Machine Learning, Communication")
experience_input = st.sidebar.text_area("Your Experience (e.g., 'Company A, Role, Dates, Responsibilities')", height=200)
education_input = st.sidebar.text_area("Your Education (e.g., 'University, Degree, Dates')", height=100)

st.sidebar.markdown("---")
st.sidebar.header("Template & Generation Options")
template_choice = st.sidebar.selectbox("Choose Resume Template", ["Professional", "Modern", "Simple"])
ai_refinement_option = st.sidebar.checkbox("Let AI refine content based on Job Description")

st.markdown("## Generated Resume Preview")

# Store resume data in a dictionary
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

# --- AI Content Generation and Refinement ---
summary_placeholder = st.empty()
final_skills_placeholder = st.empty()
final_experience_placeholder = st.empty()
final_education_placeholder = st.empty()


if st.sidebar.button("Generate/Update Resume"):
    with st.spinner("Generating and refining resume content with Gemini AI..."):
        # Generate Summary
        summary_prompt = f"""
        Generate a concise and impactful professional summary (3-4 sentences) for a resume based on the following:
        Skills: {skills_input}
        Experience: {experience_input}
        Education: {education_input}
        Job Description (for tailoring if provided): {job_description_input if job_description_input else 'N/A'}
        """
        generated_summary = generate_resume_content(summary_prompt)
        if generated_summary:
            resume_data["summary"] = generated_summary
            summary_placeholder.success("Summary generated!")
        else:
            resume_data["summary"] = "Could not generate summary. Please review input."

        # AI Refinement (if checked)
        if ai_refinement_option and job_description_input:
            st.subheader("AI Refined Sections:")
            # Refine Skills
            skills_refine_prompt = f"""
            Given the following job description and your current skills, refine and highlight the most relevant skills (comma-separated).
            Current Skills: {skills_input}
            Job Description: {job_description_input}
            Only output the refined skills, comma-separated.
            """
            refined_skills = generate_resume_content(skills_refine_prompt)
            if refined_skills:
                resume_data["skills"] = refined_skills
                final_skills_placeholder.info(f"Skills (AI Refined): {refined_skills}")
            else:
                final_skills_placeholder.warning("Could not refine skills with AI. Using original skills.")

            # Refine Experience
            experience_refine_prompt = f"""
            Given the following job description and your current work experience, rephrase and highlight achievements and responsibilities that are most relevant to the job. Focus on quantifiable results where possible.
            Current Experience: {experience_input}
            Job Description: {job_description_input}
            Provide the refined experience in a clear, bullet-point format.
            """
            refined_experience = generate_resume_content(experience_refine_prompt)
            if refined_experience:
                resume_data["experience"] = refined_experience
                final_experience_placeholder.info(f"Experience (AI Refined):\n{refined_experience}")
            else:
                final_experience_placeholder.warning("Could not refine experience with AI. Using original experience.")

            # Refine Education (less common for tailoring, but possible)
            education_refine_prompt = f"""
            Given the following job description and your education, suggest any relevant coursework or projects to highlight.
            Current Education: {education_input}
            Job Description: {job_description_input}
            Provide the refined education in a clear format.
            """
            refined_education = generate_resume_content(education_refine_prompt)
            if refined_education:
                resume_data["education"] = refined_education
                final_education_placeholder.info(f"Education (AI Refined):\n{refined_education}")
            else:
                final_education_placeholder.warning("Could not refine education with AI. Using original education.")

        else:
            st.write("AI refinement option not selected or job description not provided.")

    st.success("Resume generation complete!")

# --- Display Resume ---
st.markdown("---")

# Display profile picture
if uploaded_image is not None:
    image = Image.open(uploaded_image)
    st.image(image, caption="Profile Picture", width=150)

# Get formatted resume content
resume_content_markdown = get_resume_template(template_choice, resume_data)
st.markdown(resume_content_markdown)

st.markdown("---")
st.subheader("Download Options")

# Option to download as PDF (basic)
def create_pdf(text_content, filename="resume.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text_content)
    pdf_output = pdf.output(dest='S').encode('latin-1') # 'S' returns as string, then encode
    return pdf_output

if st.button("Download as PDF"):
    pdf_output = create_pdf(resume_content_markdown)
    st.download_button(
        label="Download PDF",
        data=pdf_output,
        file_name="generated_resume.pdf",
        mime="application/pdf"
    )

# Option to download as TXT
st.download_button(
    label="Download as Text",
    data=resume_content_markdown.encode('utf-8'),
    file_name="generated_resume.txt",
    mime="text/plain"
)

st.markdown("---")
st.info("💡 **Tips:**\n"
        "- The AI refinement is best when you provide a detailed job description.\n"
        "- Experiment with different inputs and templates.\n"
        "- For better PDF styling, consider libraries like `ReportLab` or `WeasyPrint` for HTML to PDF conversion.")
