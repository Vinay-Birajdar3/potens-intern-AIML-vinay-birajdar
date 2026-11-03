from app import config
from app.llm import get_groq_client


def detect_language(text: str):
    if text.isascii():
        return "english"

    prompt = f"""
Identify the language of the following text.

Return ONLY one of these values:

english
hindi
marathi

Text:
{text}
"""

    response = get_groq_client().chat.completions.create(
        model=config.GROQ_MODEL,
        temperature=0,
        reasoning_effort="low",
        max_completion_tokens=64,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    language = (response.choices[0].message.content or "").strip().lower()
    if language not in {"english", "hindi", "marathi"}:
        raise ValueError(f"Unsupported detected language: {language or 'empty response'}")
    return language


def translate_to_english(text: str):

    prompt = f"""
Translate the following text into English.

Return ONLY the translated text.

{text}
"""

    response = get_groq_client().chat.completions.create(
        model=config.GROQ_MODEL,
        temperature=0,
        reasoning_effort="low",
        max_completion_tokens=config.GROQ_MAX_COMPLETION_TOKENS,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    translated_text = response.choices[0].message.content
    if translated_text is None or not translated_text.strip():
        raise RuntimeError("The language model returned an empty translation.")
    return translated_text.strip()


def translate_from_english(text: str, language: str):

    if language == "english":
        return text

    prompt = f"""
Translate the following English text into {language}.

Return ONLY the translated text.

{text}
"""

    response = get_groq_client().chat.completions.create(
        model=config.GROQ_MODEL,
        temperature=0,
        reasoning_effort="low",
        max_completion_tokens=config.GROQ_MAX_COMPLETION_TOKENS,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    translated_text = response.choices[0].message.content
    if translated_text is None or not translated_text.strip():
        raise RuntimeError("The language model returned an empty translation.")
    return translated_text.strip()