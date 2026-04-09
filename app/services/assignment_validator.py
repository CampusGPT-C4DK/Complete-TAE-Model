import logging
from app.services.model_config import call_llm, get_active_model, validate_model_config

logger = logging.getLogger(__name__)


def validate_assignment(notes_text, student_text):
    """
    Validate student assignment against reference notes.
    Uses the LLM model configured in .env (Gemini, Ollama, or Mistral)
    
    Args:
        notes_text (str): Teacher's reference notes
        student_text (str): Student's assignment submission
    
    Returns:
        str: LLM response with score and feedback
    
    Raises:
        ValueError: If no model is configured or model fails
    """
    
    # Validate that a model is configured
    active_model = get_active_model()
    if not active_model:
        raise ValueError(
            "❌ No LLM model enabled in .env! "
            "Please set one of: USE_PHI3_MINI=true, USE_GEMINI=true, or USE_MISTRAL=true"
        )
    
    if not validate_model_config():
        raise ValueError(f"❌ Model configuration invalid. Active model: {active_model}")
    
    # Prepare the evaluation prompt
    prompt = f"""You are an expert teacher. Evaluate the student's assignment against the reference material.

REFERENCE MATERIAL (from teacher):
{notes_text[:2000]}

STUDENT SUBMISSION:
{student_text[:2000]}

Please provide:
1. Score (out of 10)
2. Key strengths
3. Areas for improvement
4. Overall feedback

Format your response clearly with these sections."""

    try:
        logger.info(f"🔄 Evaluating assignment using {active_model} model...")
        response = call_llm(prompt, temperature=0.3)
        logger.info("✅ Evaluation completed successfully")
        return response
    
    except Exception as e:
        logger.error(f"❌ Evaluation failed: {str(e)}")
        raise