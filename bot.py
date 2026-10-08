import os
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
class FakeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), FakeHandler)
    server.serve_forever()
threading.Thread(target=run_fake_server, daemon=True).start()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from voix import faire_voix
from niveaux import CHIFFRES_1, EXERCICES
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

async def demarrer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['niveau'] = 1
    context.user_data['vus'] = set()
    context.user_data['exercice_index'] = 0
    await update.message.reply_text("🚀 Mission 1: Les chiffres de 0 à 10! Envoie-les tous!")
    fichier = await faire_voix("Mission un! Les chiffres de zéro à dix!")
    with open(fichier, "rb") as f:
        await update.message.reply_voice(voice=f)
    os.remove(fichier)

async def envoyer_exercice(chat_id, context):
    index = context.user_data.get('exercice_index', 0)
    if index >= len(EXERCICES):
        # Кнопка Recommencer
        clavier = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Recommencer", callback_data="recommencer")]
        ])
        with open("champion.png", "rb") as photo:
            await context.bot.send_photo(
                chat_id=chat_id, 
                photo=photo, 
                caption="🏆 Bravo! Tu as réussi tous les calculs! 6/6 🎉",
                reply_markup=clavier
            )
        fichier = await faire_voix("Bravo! Tu es un champion! Tu veux recommencer?")
        with open(fichier, "rb") as f:
            await context.bot.send_voice(chat_id=chat_id, voice=f)
        os.remove(fichier)
        return
    ex = EXERCICES[index]

    # ГАРНІ КНОПКИ!
    boutons = [
        InlineKeyboardButton(f"🔵 {ex['choix'][0]}", callback_data=f"rep_{ex['choix'][0]}"),
        InlineKeyboardButton(f"🟠 {ex['choix'][1]}", callback_data=f"rep_{ex['choix'][1]}")
    ]

    # Можна ще додати кнопку-підказку
    clavier = [
        boutons,
        [InlineKeyboardButton("💡 Aide", callback_data="aide")]
    ]

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🧮 *Niveau 2* - Question {index+1}/{len(EXERCICES)}\n\n✨ *{ex['q']}* ✨\n\nChoisis la bonne réponse 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )
    fichier = await faire_voix(ex['q'].replace("=","égale").replace("+","plus"))
    with open(fichier, "rb") as f:
        await context.bot.send_voice(chat_id=chat_id, voice=f)
    os.remove(fichier)

async def repondre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texte = update.message.text.strip()
    if context.user_data.get('niveau', 1) == 1 and texte in CHIFFRES_1:
        vus = context.user_data.get('vus', set())
        vus.add(texte)
        context.user_data['vus'] = vus
        await update.message.reply_text(f"✅ {texte} -> {CHIFFRES_1[texte]} ({len(vus)}/{len(CHIFFRES_1)})")
        fichier = await faire_voix(CHIFFRES_1[texte])
        with open(fichier, "rb") as f:
            await update.message.reply_voice(voice=f)
        os.remove(fichier)
        if len(vus) == len(CHIFFRES_1):
            clavier = [[InlineKeyboardButton("➡️ Passer au Niveau 2 🚀", callback_data="niveau2")]]
            await update.message.reply_text("🌟 Bravo! Prêt pour les calculs? 👇", reply_markup=InlineKeyboardMarkup(clavier))

async def gerer_boutons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get('exercice_index', 0)
    if query.data == "recommencer":
        context.user_data['niveau'] = 1
        context.user_data['vus'] = set()
        context.user_data['exercice_index'] = 0
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🚀 Mission 1: Les chiffres de 0 à 10! Envoie-les tous!"
        )
        fichier = await faire_voix("Mission un! Les chiffres de zéro à dix!")
        with open(fichier, "rb") as f:
            await context.bot.send_voice(chat_id=query.message.chat_id, voice=f)
        os.remove(fichier)
        return
    if query.data == "niveau2":
        context.user_data['niveau'] = 2
        context.user_data['exercice_index'] = 0
        await query.edit_message_text("🔥 Niveau 2 débloqué! 🧮")
        await envoyer_exercice(query.message.chat_id, context)
    elif query.data == "aide":
        ex = EXERCICES[idx]
        n1 = ex["n1"]
        n2 = ex["n2"]
        pommes_rouges = "🍎 " * n1
        pommes_vertes = "🍏 " * n2
        texte_aide = f"💡 Aide - Compte!\n\n{pommes_rouges} + {pommes_vertes}\n\n👉 {n1} rouges + {n2} vertes =?\nCompte avec tes doigts! ☝️"
        await context.bot.send_message(chat_id=query.message.chat_id, text=texte_aide)
        fichier = await faire_voix(f"Compte les pommes! {n1} plus {n2}")
        with open(fichier, "rb") as f:
            await context.bot.send_voice(chat_id=query.message.chat_id, voice=f)
        os.remove(fichier)    
    elif query.data.startswith("rep_"):
        choix = query.data.split("_")[1]
        if choix == EXERCICES[idx]["rep"]:
            await query.edit_message_text(f"✅ {EXERCICES[idx]['q']} {choix} - Correct! 🎉")
            fichier = await faire_voix("Bravo! C'est correct!")
            with open(fichier, "rb") as f:
                await context.bot.send_voice(chat_id=query.message.chat_id, voice=f)
            os.remove(fichier)
            context.user_data['exercice_index'] = idx + 1
            await envoyer_exercice(query.message.chat_id, context)
        else:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Essaye encore! 🙏 Ce n'est pas {choix}")
            ex = EXERCICES[idx]
            boutons = [InlineKeyboardButton(c, callback_data=f"rep_{c}") for c in ex["choix"]]
            await context.bot.send_message(chat_id=query.message.chat_id, text=ex['q'], reply_markup=InlineKeyboardMarkup([boutons]))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", demarrer))
    app.add_handler(CallbackQueryHandler(gerer_boutons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, repondre))
    print("Bot en mode blocs lancé!")
    app.run_polling()

if __name__ == "__main__":
    main()
