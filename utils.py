import os
import fitz  
from flask import current_app
import google.generativeai as genai

def extract_text_from_pdf(pdf_path):
    """Extracts all text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text("text")
        doc.close()
        return text
    except Exception as e:
        current_app.logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return None

def summarize_text_with_google_ai(text_content, model_name="gemma-3-27b-it"): 
    """Summarizes text using the Google Generative AI API."""
    api_key = current_app.config.get("GOOGLE_API_KEY")
    if not api_key:
        current_app.logger.error("Google API key not configured.")
        return "Error: Google API key not configured. Please set it in your environment variables."

    if not text_content:
        current_app.logger.warning("No text content provided for summarization.")
        return None

    genai.configure(api_key=api_key)

    
    generation_config = {
        "temperature": 0.3,
        "top_p": 1.0,
        "top_k": 32,  
        "max_output_tokens": 300,
    }
    safety_settings = [ 
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        max_chars = 15000
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars]
            current_app.logger.info(f"Text content truncated to {max_chars} characters for Google AI summarization.")

        prompt = f"Please provide a concise summary (around 150-200 words), do not include preambule like 'here is your summary' for the following document content:\n\n{text_content}"

        response = model.generate_content(prompt)
        
        if response.parts:
            summary = "".join(part.text for part in response.parts)
        elif hasattr(response, 'text'):
             summary = response.text
        else:

            current_app.logger.warning(f"Could not directly access text from Google AI response. Full response: {response.prompt_feedback}") 
            if response.candidates and response.candidates[0].content.parts:
                summary = "".join(part.text for part in response.candidates[0].content.parts)
            else:
                summary = "Error: Could not extract summary from Google AI response."

        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason_message = f"Content generation blocked. Reason: {response.prompt_feedback.block_reason}."
            if response.prompt_feedback.safety_ratings:
                block_reason_message += f" Safety Ratings: {response.prompt_feedback.safety_ratings}"
            current_app.logger.error(block_reason_message)
            return f"Error: {block_reason_message}"


        return summary.strip()

    except Exception as e:
        current_app.logger.error(f"Error during Google AI summarization: {e}")
        return f"Error: An issue occurred while generating the summary with Google AI: {str(e)}"


def generate_and_store_summary_for_course(course, material_filename):
    """
    Orchestrates text extraction, summarization (now with Google AI),
    and storing the summary in the course object.
    Modifies course.material_summary in place.
    Returns True on success, False on failure to generate/store summary.
    """
    if not material_filename or not material_filename.lower().endswith('.pdf'):
        current_app.logger.info(f"Material '{material_filename}' is not a PDF. Skipping summary for course ID {getattr(course, 'id', 'None')}.")
        course.material_summary = None
        return True

    upload_folder_abs = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
    full_pdf_path = os.path.join(upload_folder_abs, material_filename)

    if not os.path.exists(full_pdf_path):
        current_app.logger.error(f"PDF file not found at {full_pdf_path} for summarization (Course ID: {getattr(course, 'id', 'None')}).")
        course.material_summary = "Error: PDF file not found for summarization."
        return False

    current_app.logger.info(f"Extracting text from: {full_pdf_path} for course ID {getattr(course, 'id', 'None')}.")
    extracted_text = extract_text_from_pdf(full_pdf_path)

    if extracted_text:
        current_app.logger.info(f"Text extracted (length: {len(extracted_text)}). Summarizing with Google AI for course ID {getattr(course, 'id', 'None')}...")
        summary = summarize_text_with_google_ai(extracted_text) 
        if summary and not summary.startswith("Error:"):
            course.material_summary = summary
            current_app.logger.info(f"Google AI summary generated and set for course ID {getattr(course, 'id', 'None')}.")
            return True
        else:
            course.material_summary = summary 
            current_app.logger.error(f"Google AI summary generation failed for course ID {getattr(course, 'id', 'None')}. Reason: {summary}")
            return False
    else:
        course.material_summary = "Error: Failed to extract text from PDF."
        current_app.logger.error(f"Text extraction failed for PDF: {full_pdf_path} (Course ID: {getattr(course, 'id', 'None')}).")
        return False
