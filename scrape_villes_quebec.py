"""
scrape_villes_quebec.py
Récupère la page Wikipedia (fr) "Liste des villes du Québec",
parse la table principale et écrit un fichier JSON "villes_quebec.json".
Dépendances: requests, beautifulsoup4
Installer: pip install requests beautifulsoup4
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

WIKI_URL = "https://fr.wikipedia.org/wiki/Liste_des_villes_du_Qu%C3%A9bec"
OUTFILE = "villes_quebec.json"

def clean_text(s):
    if s is None:
        return None
    s = s.strip()
    # enlever les notes entre crochets [1], [N 2], etc
    s = re.sub(r'\[\s*[^]]+\]', '', s)
    # normaliser espaces
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def parse_coord(coord_text):
    # Récupère coordonnées présentes sous forme "45° 39′ 00″ N, 72° 34′ 00″ O"
    if not coord_text:
        return None
    coord_text = coord_text.replace('\xa0',' ')
    return coord_text.strip()

def try_float(s):
    try:
        return float(s.replace('\u00A0','').replace(' ', '').replace(',', '.'))
    except Exception:
        return None

def parse_table(table):
    # Attendu: la table a des <tr> dont les cellules sont <th> (header) et <td>.
    rows = []
    header_cells = []
    thead = table.find('tr')
    if thead:
        for th in thead.find_all(['th','td']):
            header_cells.append(clean_text(th.get_text()))
    # Parcourir les autres lignes
    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all(['td','th'])
        if not tds:
            continue
        # Certaines lignes peuvent être des séparateurs, on ignore si colonnes insuffisantes
        if len(tds) < 6:
            continue
        # On lit champs: Code, Nom, MRC, Région, Population, Superficie (km²), Densité, Date, Coordonnées
        # Bibliothèque : on extrait le texte cell par cell et on nettoie
        cells = [clean_text(td.get_text()) for td in tds]
        # Normaliser longueur: on essaie d'identifier les colonnes clé par nom si header connu
        # Mais ici on suppose ordre: Code | Nom | MRC | Région | Estimation de population | Superficie (km²) | Densité | Date de fondation | Coordonnées
        # On tolère les colonnes supplémentaires en gardant les premières 9 champs utiles.
        entry = {}
        # safe indexing
        def cell(i): return cells[i] if i < len(cells) else None

        entry['code'] = cell(0)
        entry['nom'] = cell(1)
        entry['mrc'] = cell(2)
        entry['region'] = cell(3)
        # population : enlever espace insécable, points, etc -> int si possible
        pop_raw = cell(4)
        if pop_raw:
            pop_clean = re.sub(r'[^\d]', '', pop_raw)
            entry['population_estimee'] = int(pop_clean) if pop_clean.isdigit() else pop_raw
        else:
            entry['population_estimee'] = None
        # superficie
        superficie_raw = cell(5)
        entry['superficie_km2'] = try_float(superficie_raw)
        # densité
        dens_raw = cell(6)
        entry['densite_hab_par_km2'] = try_float(dens_raw)
        # date fondation / incorporation (peut être sur 1 ou 2 cellules)
        # Certains tableaux ont la date répartie sur 2 cellules (jour / mois / année). On concatène celles qui suivent.
        # Regroupons la cellule 7 et 8 si elles existent et ressemblent à une date.
        date_parts = []
        if 7 < len(cells):
            date_parts.append(cell(7))
        if 8 < len(cells):
            # si la cellule 8 contient des chiffres ou mots de mois, on l'ajoute
            date_parts.append(cell(8))
        date_concat = ' '.join([p for p in date_parts if p])
        date_concat = clean_text(date_concat) if date_concat else None
        entry['date_fondation_incorporation'] = date_concat
        # coordonnées généralement à la dernière cellule
        coord_raw = cell(9) if len(cells) > 9 else (cell(8) if len(cells) == 9 else None)
        entry['coordonnees'] = parse_coord(coord_raw)
        # lien wikidata si disponible (on peut chercher une balise <a> dans la cellule Nom)
        try:
            nom_td = tds[1]
            a = nom_td.find('a', href=True)
            if a:
                entry['wiki_url'] = "https://fr.wikipedia.org" + a['href']
            else:
                entry['wiki_url'] = None
        except Exception:
            entry['wiki_url'] = None

        rows.append(entry)
    return rows


def main():
    print("Téléchargement de la page...", WIKI_URL)
    resp = requests.get(WIKI_URL, headers={"User-Agent":"scraper-bot/1.0 (+https://example.org)"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Trouver la première table qui correspond au tableau de villes.
    # Sur la page, le tableau principal est généralement une 'wikitable' ou un tableau responsive.
    table = None
    for t in soup.find_all('table'):
        cls = t.get('class') or []
        if any('wikitable' in c for c in cls) or 'sortable' in ' '.join(cls):
            # heuristique: la table qui a "Estimation de population" dans le header
            header_text = t.get_text().lower()
            if 'estimation' in header_text and 'population' in header_text:
                table = t
                break
    if table is None:
        # fallback: prendre la première table du document
        tables = soup.find_all('table')
        if tables:
            table = tables[0]
    if table is None:
        raise RuntimeError("Impossible de localiser le tableau des villes sur la page.")

    print("Parsing du tableau...")
    data = parse_table(table)
    print(f"{len(data)} villes extraites (approx.). Écriture du fichier {OUTFILE} ...")
    with open(OUTFILE, 'w', encoding='utf-8') as f:
        json.dump({
            "source_url": WIKI_URL,
            "date_extraction_utc": datetime.utcnow().isoformat() + "Z",
            "nombre_villes": len(data),
            "villes": data
        }, f, ensure_ascii=False, indent=2)
    print("Terminé. Fichier :", OUTFILE)

if __name__ == "__main__":
    main()
