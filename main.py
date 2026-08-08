import random
import discord
from discord.ext import commands

# ---------------------------------------------------------
# CONFIGURATION ET INITIALISATION
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# "Bases de données" temporaires en mémoire
joueurs = {}
boutique = {
    "Telephone": {"prix": 500, "desc": "Un smartphone pour communiquer"},
    "Voiture": {"prix": 15000, "desc": "Un véhicule de ville basique"},
    "Kit de Soin": {"prix": 150, "desc": "Permet de se soigner en RP"},
    "Pistolet": {"prix": 3000, "desc": "Arme de poing légère (Permis requis)"}
}

def get_joueur(user_id):
    """Initialise les données d'un joueur s'il n'existe pas encore."""
    if user_id not in joueurs:
        joueurs[user_id] = {
            "fiche": None,
            "portefeuille": 500,  # Argent de départ
            "banque": 1000,
            "inventaire": []
        }
    return joueurs[user_id]


@bot.event
async def on_ready():
    print(f"✅ Bot RP connecté en tant que : {bot.user.name}")
    print("----------------------------------------------")


# ---------------------------------------------------------
# 1. SYSTÈME DE FICHE RP
# ---------------------------------------------------------
@bot.command(name="creer-fiche")
async def creer_fiche(ctx, nom: str, age: int, metier: str, *, histoire: str = "Non renseignée"):
    """Crée ou met à jour la fiche RP du joueur.
    Usage: !creer-fiche "Jean Dupont" 25 "Policier" Un ancien militaire reconverti...
    """
    p = get_joueur(ctx.author.id)
    p["fiche"] = {
        "nom": nom,
        "age": age,
        "metier": metier,
        "histoire": histoire
    }
    
    embed = discord.Embed(
        title="✅ Fiche Personnage Créée",
        description=f"La fiche de **{nom}** a été enregistrée avec succès.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command(name="fiche")
async def voir_fiche(ctx, membre: discord.Member = None):
    """Affiche la fiche RP d'un membre (ou la sienne si aucun membre spécifié)."""
    target = membre or ctx.author
    p = get_joueur(target.id)
    
    if not p["fiche"]:
        await ctx.send(f"❌ **{target.display_name}** n'a pas encore créé de fiche RP (`!creer-fiche`).")
        return

    f = p["fiche"]
    embed = discord.Embed(
        title=f"🎭 Carte d'Identité : {f['nom']}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Nom & Prénom", value=f["nom"], inline=True)
    embed.add_field(name="Âge", value=f"{f['age']} ans", inline=True)
    embed.add_field(name="Métier", value=f["metier"], inline=True)
    embed.add_field(name="Histoire / Bio", value=f["histoire"], inline=False)
    embed.set_footer(text=f"Joueur : {target.display_name}")

    await ctx.send(embed=embed)


# ---------------------------------------------------------
# 2. SYSTÈME D'ÉCONOMIE & BOUTIQUE
# ---------------------------------------------------------
@bot.command(name="banque")
async def solde(ctx):
    """Affiche le solde du portefeuille et du compte bancaire."""
    p = get_joueur(ctx.author.id)
    embed = discord.Embed(title=f"💳 Compte Bancaire - {ctx.author.display_name}", color=discord.Color.gold())
    embed.add_field(name="💵 Portefeuille", value=f"{p['portefeuille']} $", inline=True)
    embed.add_field(name="🏦 Banque", value=f"{p['banque']} $", inline=True)
    embed.add_field(name="💰 Total", value=f"{p['portefeuille'] + p['banque']} $", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="travail")
@commands.cooldown(1, 3600, commands.BucketType.user)  # Une fois par heure
async def travail(ctx):
    """Permet de travailler pour gagner un salaire."""
    p = get_joueur(ctx.author.id)
    gain = random.randint(150, 400)
    p["portefeuille"] += gain
    
    embed = discord.Embed(
        title="💼 Service Terminé",
        description=f"Vous avez travaillé dur et gagné **{gain} $** !",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@travail.error
async def travail_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes = int(error.retry_after // 60)
        await ctx.send(f"⏳ Vous devez vous reposer ! Réessayez dans **{minutes} minute(s)**.")


@bot.command(name="deposer")
async def deposer(ctx, montant: int):
    """Dépose de l'argent du portefeuille vers la banque."""
    p = get_joueur(ctx.author.id)
    if montant <= 0 or p["portefeuille"] < montant:
        await ctx.send("❌ Vous n'avez pas assez d'argent liquide.")
        return

    p["portefeuille"] -= montant
    p["banque"] += montant
    await ctx.send(f"🏦 Vous avez déposé **{montant} $** sur votre compte bancaire.")


@bot.command(name="retirer")
async def retirer(ctx, montant: int):
    """Retire de l'argent de la banque vers le portefeuille."""
    p = get_joueur(ctx.author.id)
    if montant <= 0 or p["banque"] < montant:
        await ctx.send("❌ Vous n'avez pas assez d'argent en banque.")
        return

    p["banque"] -= montant
    p["portefeuille"] += montant
    await ctx.send(f"💵 Vous avez retiré **{montant} $** de votre compte.")


@bot.command(name="boutique")
async def afficher_boutique(ctx):
    """Affiche les articles disponibles à l'achat."""
    embed = discord.Embed(title="🛒 Boutique de la Ville", color=discord.Color.purple())
    for item, info in boutique.items():
        embed.add_field(
            name=f"{item} — {info['prix']} $",
            value=info["desc"],
            inline=False
        )
    embed.set_footer(text="Utilisez !acheter <nom_objet> pour commander.")
    await ctx.send(embed=embed)


@bot.command(name="acheter")
async def acheter(ctx, *, item_nom: str):
    """Achete un objet dans la boutique."""
    # Recherche insensible à la casse
    item_key = next((k for k in boutique if k.lower() == item_nom.lower()), None)
    
    if not item_key:
        await ctx.send("❌ Cet objet n'existe pas dans la boutique (`!boutique`).")
        return

    prix = boutique[item_key]["prix"]
    p = get_joueur(ctx.author.id)

    if p["portefeuille"] < prix:
        await ctx.send(f"❌ Vous n'avez pas assez d'argent liquide sur vous ({prix} $ requis).")
        return

    p["portefeuille"] -= prix
    p["inventaire"].append(item_key)
    await ctx.send(f"🛍️ Vous avez acheté **{item_key}** pour **{prix} $** !")


@bot.command(name="inventaire")
async def inventaire(ctx):
    """Affiche votre sac à dos / inventaire."""
    p = get_joueur(ctx.author.id)
    inv = p["inventaire"]

    embed = discord.Embed(title=f"🎒 Inventaire de {ctx.author.display_name}", color=discord.Color.dark_orange())
    if not inv:
        embed.description = "Votre sac est vide."
    else:
        # Compte le nombre d'exemplaires par objet
        counts = {item: inv.count(item) for item in set(inv)}
        lignes = [f"• **{item}** x{count}" for item, count in counts.items()]
        embed.description = "\n".join(lignes)

    await ctx.send(embed=embed)


# ---------------------------------------------------------
# 3. OUTILS ET ACTIONS RP
# ---------------------------------------------------------
@bot.command(name="roll")
async def roll(ctx, de_max: int = 100):
    """Lance un dé RP personnalisé (par défaut sur 100)."""
    res = random.randint(1, de_max)
    await ctx.send(f"🎲 **{ctx.author.display_name}** lance un dé ({de_max}) et obtient : **{res}**")


@bot.command(name="me")
async def action_me(ctx, *, action: str):
    """Exécute une action RP pour votre personnage."""
    await ctx.message.delete()  # Supprime le message de commande
    await ctx.send(f"🎭 **{ctx.author.display_name}** {action}")


@bot.command(name="do")
async def action_do(ctx, *, description: str):
    """Décrit une situation ou un environnement RP."""
    await ctx.message.delete()
    await ctx.send(f"📜 *[Environnement / Action]* : **{description}**")


# ---------------------------------------------------------
# LANCEMENT DU BOT
# ---------------------------------------------------------
TOKEN = "MTUzNTI5NjcwMzA5ODM5Njc0NQ.GH6fL2.XupOKm0fhYcBny1L32ez3xrTeXBUOOv9yWkgog"

if __name__ == "__main__":
    bot.run(TOKEN)


