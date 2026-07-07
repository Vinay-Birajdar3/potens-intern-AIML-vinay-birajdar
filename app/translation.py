from groq import Groq

from app import config

client = Groq(api_key=config.GROQ_API_KEY)


def detect_language(text: str):

    prompt = f"""
Identify the language of the following text.

Return ONLY one of these values:

english
hindi
marathi

Text:
{text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip().lower()


def translate_to_english(text: str):

    prompt = f"""
Translate the following text into English.

Return ONLY the translated text.

{text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()


def translate_from_english(text: str, language: str):

    if language == "english":
        return text

    prompt = f"""
Translate the following English text into {language}.

Return ONLY the translated text.

{text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()