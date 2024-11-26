import os
import pandas as pd
from simpledbf import Dbf5
import dbf
import logging
from datetime import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Désactiver l'interface Tkinter
Tk().withdraw()

# Configuration du logger
log_folder = './logs'
os.makedirs(log_folder, exist_ok=True)
log_file = os.path.join(log_folder, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("Début du script")

try:
    # Sélection dynamique des fichiers
    logging.info("Demander à l'utilisateur de choisir les fichiers...")
    print("Sélectionnez le fichier DBF existant.")
    dbf_file_path = askopenfilename(filetypes=[("DBF Files", "*.dbf")])
    if not dbf_file_path:
        raise FileNotFoundError("Aucun fichier DBF sélectionné.")

    print("Sélectionnez le fichier XLSX contenant les nouvelles données.")
    xlsx_file_path = askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
    if not xlsx_file_path:
        raise FileNotFoundError("Aucun fichier XLSX sélectionné.")

    output_dbf_path = os.path.splitext(dbf_file_path)[0] + "_final.dbf"

    # Charger les données du fichier DBF existant
    logging.info(f"Chargement du fichier DBF existant : {dbf_file_path}")
    dbf_reader = Dbf5(dbf_file_path)
    dbf_df = dbf_reader.to_dataframe()

    # Charger les données du fichier XLSX contenant les nouvelles données
    logging.info(f"Chargement du fichier XLSX : {xlsx_file_path}")
    xlsx_df = pd.read_excel(xlsx_file_path)

    # Nettoyer les champs vides dans le fichier XLSX
    logging.info("Nettoyage des champs vides dans le fichier XLSX...")
    xlsx_df = xlsx_df.dropna(how='all')  # Supprime les lignes entièrement vides
    xlsx_df = xlsx_df.fillna('')         # Remplace les NaN par des chaînes vides

    # Vérification des colonnes
    logging.info("Vérification des colonnes entre le fichier DBF et XLSX...")
    if set(dbf_df.columns) != set(xlsx_df.columns):
        logging.error("Les colonnes du DBF et du XLSX ne correspondent pas.")
        raise ValueError("Les colonnes du DBF et du XLSX ne correspondent pas.")

    # Harmoniser l'ordre des colonnes
    xlsx_df = xlsx_df[dbf_df.columns]

    # Fusionner les données : inclure les données de l'ancien DBF et les nouvelles du XLSX
    logging.info("Fusion des données des deux fichiers...")
    merged_df = pd.concat([dbf_df, xlsx_df], ignore_index=True)

    # Conversion stricte des données en texte
    merged_df = merged_df.astype(str)

    # Vérification du nombre total de lignes après fusion
    logging.info(f"Nombre total de lignes après fusion : {len(merged_df)}")

    # Sauvegarde temporaire en CSV (pour vérification)
    output_csv = output_dbf_path.replace('.dbf', '.csv')
    merged_df.to_csv(output_csv, index=False)
    logging.info(f"Fichier fusionné sauvegardé en CSV pour vérification : {output_csv}")

    # Conversion du DataFrame fusionné en DBF
    logging.info("Conversion du DataFrame final en DBF...")
    field_specs = ";".join([f"{col} C(255)" for col in merged_df.columns])  # Spécifications des champs
    dbf_table = dbf.Table(output_dbf_path, field_specs)
    dbf_table.open(mode=dbf.READ_WRITE)

    # Ajouter chaque ligne fusionnée au nouveau fichier DBF
    for _, row in merged_df.iterrows():
        dbf_table.append(tuple(row))  # Conversion en tuple avant ajout

    dbf_table.close()
    logging.info(f"Fichier DBF final sauvegardé : {output_dbf_path}")

except Exception as e:
    logging.exception("Une erreur est survenue")
    print(f"Erreur : {e}")

logging.info("Fin du script")
