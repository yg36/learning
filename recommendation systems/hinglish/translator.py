from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


def translate_hinglish(text):

    try:

        hindi = transliterate(
            text,
            sanscript.ITRANS,
            sanscript.DEVANAGARI
        )

        return hindi

    except:

        return text