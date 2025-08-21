# utils.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from fpdf import FPDF

# --- CONSTANTES GLOBAIS ---
JSON_PATH = "projects.json"
HISTORICO_DIRETO_PATH = "historico_direto.json"
HISTORICO_INDIRETO_PATH = "historico_indireto.json"

TIPOS_PAVIMENTO = {
    "Área Privativa (Autônoma)": (1.00, 1.00), "Áreas de lazer ambientadas": (2.00, 4.00), "Varandas": (0.75, 1.00),
    "Terraços / Áreas Descobertas": (0.30, 0.60), "Garagem (Subsolo)": (0.50, 0.75), "Estacionamento (terreno)": (0.05, 0.10),
    "Salas com Acabamento": (1.00, 1.00), "Salas sem Acabamento": (0.75, 0.90), "Loja sem Acabamento": (0.40, 0.60),
    "Serviço (unifam. baixa, aberta)": (0.50, 0.50), "Barrilete / Cx D'água / Casa Máquinas": (0.50, 0.75),
    "Piscinas": (0.50, 0.75), "Quintais / Calçadas / Jardins": (0.10, 0.30), "Projeção Terreno sem Benfeitoria": (0.00, 0.00),
}
DEFAULT_PAVIMENTO = {"nome": "Pavimento Tipo", "tipo": "Área Privativa (Autônoma)", "rep": 1, "coef": 1.00, "area": 100.0, "constr": True}

ETAPAS_OBRA = {
    "Serviços Preliminares e Fundações":       (7.0, 8.0, 9.0),
    "Estrutura (Supraestrutura)":              (14.0, 16.0, 22.0),
    "Vedações (Alvenaria)":                    (8.0, 10.0, 15.0),
    "Cobertura e Impermeabilização":           (4.0, 5.0, 8.0),
    "Revestimentos de Fachada":                (5.0, 6.0, 10.0),
    "Instalações (Elétrica e Hidráulica)":      (12.0, 15.0, 18.0),
    "Esquadrias (Portas e Janelas)":           (6.0, 8.0, 12.0),
    "Revestimentos de Piso":                   (8.0, 10.0, 15.0),
    "Revestimentos de Parede":                 (6.0, 8.0, 12.0),
    "Revestimentos de Forro":                  (3.0, 4.0, 6.0),
    "Pintura":                                 (4.0, 5.0, 8.0),
    "Serviços Complementares e Externos":      (3.0, 5.0, 10.0)
}

DEFAULT_CUSTOS_INDIRETOS = {
    "IRPJ/ CS/ PIS/ COFINS":       (3.0, 4.0, 6.0),
    "Corretagem":                      (3.0, 3.61, 5.0),
    "Publicidade":                       (0.5, 0.9, 2.0),
    "Manutenção":                      (0.3, 0.5, 1.0),
    "Custo Fixo da Incorporadora": (3.0, 4.0, 6.0),
    "Assessoria Técnica":                (0.5, 0.7, 1.5),
    "Projetos":                          (0.4, 0.52, 1.5),
    "Licenças e Incorporação":         (0.1, 0.2, 0.5),
    "Outorga Onerosa":                 (0.0, 0.0, 2.0),
    "Condomínio":                      (0.0, 0.0, 0.5),
    "IPTU":                            (0.05, 0.07, 0.2),
    "Preparação do Terreno":           (0.2, 0.33, 1.0),
    "Financi
