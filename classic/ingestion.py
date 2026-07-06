"""
============
Orchestrateur du pipeline d'ingestion.

Ce module coordonne l'ensemble du processus d'ingestion des articles
scientifiques. Il appelle successivement toutes les étapes nécessaires à la
construction de la base vectorielle :

    - téléchargement des articles ;
    - extraction et nettoyage du texte ;
    - extraction des métadonnées ;
    - découpage en chunks ;
    - génération des embeddings ;
    - indexation dans la base vectorielle.
"""
