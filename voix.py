import edge_tts

VOIX_ENFANT = "fr-FR-HenriNeural"

async def faire_voix(texte):
    communicate = edge_tts.Communicate(
        texte,
        VOIX_ENFANT,
        pitch='+50Hz',
        rate='-5%'
    )
    await communicate.save("voix.mp3")
    return "voix.mp3"