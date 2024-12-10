#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import fitz
import pytesseract
import os
from pdf2image import convert_from_path
import io
from pdf2image import convert_from_bytes
import cv2
import numpy as np
from PIL import Image
from fpdf import FPDF
import streamlit as st
import pandas as pd
import os
from streamlit_option_menu import option_menu
import requests
import json
from unidecode import unidecode
import gspread
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd
import streamlit as st
import time
import requests
import base64
import json
import pandas as pd
from unidecode import unidecode
import gspread
import base64
import hashlib
import io
from base64 import b64decode
from datetime import datetime, date, timedelta
import os
from zipfile import ZipFile
import zipfile
from io import BytesIO
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import random
import smtplib
import email.message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import re

def nfTrata(nfNumber):
    
    nfTratada = ''
    for i, caract in enumerate(nfNumber):
        if caract != '0':
            nfTratada = nfNumber[i:]
            nfTratada = nfTratada.lower()
            break
            
    return nfTratada



def convert_pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")  # Abre o PDF diretamente a partir dos bytes
    images = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)  # Carrega a página do PDF
        pix = page.get_pixmap(dpi=300)  # Converte a página para uma imagem (pixmap)
        img_bytes = pix.tobytes("png")  # Converte o pixmap para bytes em formato PNG
        img = Image.open(io.BytesIO(img_bytes))  # Cria a imagem usando PIL
        images.append(img)
        break
    return images


# Função para pré-processar imagens
def preprocess_image(img_bytes):
    
    np_img = np.array(Image.open(img_bytes).convert('L'))  # Converte para escala de cinza
    
    # Ajustar brilho e contraste
    alpha = 1.5  # Contraste
    beta = 50    # Brilho
    adjusted = cv2.convertScaleAbs(np_img, alpha=alpha, beta=beta)
    
    # Aplicar desfoque gaussiano para suavizar ruídos
    blurred = cv2.GaussianBlur(adjusted, (5, 5), 0)
    
    # Aplicar binarização (Otsu Thresholding)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Aplicar nitidez usando um kernel de convolução
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(binary, -1, kernel)
    
    return sharpened


# Função para extrair texto com Tesseract
def extract_text_from_image(image_path): 

    # Configuração local para Tesseract
    #pytesseract.pytesseract.tesseract_cmd = os.path.join(os.getcwd(), "assets", "tesseract.exe")

    # Configuração de idioma para Tesseract
    traineddata_path = os.path.join(os.getcwd(), "assets", "por.traineddata")
    config = f'--oem 3 --psm 6 -l por --tessdata-dir "{os.path.dirname(traineddata_path)}"'

    txt = pytesseract.image_to_string(image_path, config=config).lower()
    return txt
  
    
    
def startMediumPointOcr():
    st.session_state.validTax = ''
    st.session_state.authCods = [
                                    "37.01.01",
                                    "35.01.02",
                                    "23.01.01",
                                    "17.06.04",
                                    "17.06.01",
                                    "17.02.04",
                                    "17.02.02",
                                    "13.05.07",
                                    "13.03.01",
                                    "13.02.01",
                                    "12.13.01",
                                    "10.08.01",
                                    "08516",
                                    "06808",
                                    "06777",
                                    "06394",
                                    "06.04.01",
                                    "03.02.01",
                                    "02919",
                                    "02496",
                                    "01.09.02",
                                    "01.03.01",
                              ]
    st.session_state.docNfOcr = ''
    st.session_state.valueDocOcr = ''
    st.session_state.codServOcr = ''
    st.session_state.numberNfOcr = ''
    st.session_state.dtEmissaoOcr = ''
    st.session_state.txtOcr = ''

    #lendo arquivo em bytes
    pdf_bytes = st.session_state.arquivoObjectToOcr.read()

    # Converte bytes para imagens
    images = convert_pdf_to_images(pdf_bytes)



    for idx, img in enumerate(images):
        # Converte PIL Image para BytesIO
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Pré-processar a imagem
        preprocessed_image = preprocess_image(img_byte_arr)
        
        # Converte imagem pré-processada (numpy array) para PIL
        preprocessed_pil_image = Image.fromarray(preprocessed_image)
        
        # Extrair texto da imagem
        st.session_state.txtOcr = extract_text_from_image(preprocessed_pil_image)
        break
  

    if ('recebido' not in st.session_state.txtOcr) and (('prefeitura do município de são paulo' in st.session_state.txtOcr) or ('nota carioca' in st.session_state.txtOcr) or ('prefeitura do municipio de são paulo' in st.session_state.txtOcr) or ('intermediário do serviço' in st.session_state.txtOcr and 'danfse v1.0' in st.session_state.txtOcr)):
        st.write(st.session_state.txtOcr)
        listValue = []
        listDate = []
        listNumberNf = []
        listCodServ = []
        listDocNf = []

        #PMSP
        patternDatePmsp = r'(?:emissão|paulo)[^\d]*(\d{2}/\d{2}/\d{4})|(?:emissão|paulo).*(\d{2}/\d{2}/\d{4})|(?:emissão|paulo)\s*(\d{2}/\d{2}/\d{4})|(?:emissão|paulo)\s*.\s*(\d{2}/\d{2}/\d{4})'
        patternNumberNfPmsp = r'nf=\s*(\d{8})|paulo\s+(\d{8})|nota\s*(\d{8})|nf=(\d{1,8})'
        patternValuePmsp = r'total do serviço = r\$ \d{1,3}\.\d{1,3},\d{2}|total do serviço = r\$ \d{1,3},\d{2}'
        patternCodServPmsp = r'serviço\s*\d{5} - '
        patternDocNfPmsp = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|cpf/cnpj\: \d{2}\.\d{3}\.\d{3}/\d{4} \d{2}|cpf/cnpj\: \d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|cpf/cnpj\. \d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|cpf/cnpj \d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
        #risco error: date, codServ

        #PMRJ
        patternValuePmrj = r'valor da nota = r\$ \d{1,3}\.\d{3},\d{2}|valor da nota = r\$ \d{1,3},\d{2}'
        patternNumberNfPmrj = r"rio de janeiro (\d{8})"
        patternCodServPmrj = r'(\d{2}\.){2}\d{2} - '
        patternDocNfPmrj = patternDocNfPmsp
        patternDatePmrj = patternDatePmsp

        #govFederal
        patternDateGovFederal = r'competência da nfs-e\s*.*?(\d{2}/\d{2}/\d{4})|emissão da nfs-e\s*.*?(\d{2}/\d{2}/\d{4})|emissão da nfs-e\s*(\d{2}/\d{2}/\d{4})'
        patternNumberNfGovFederal = r'mero da nfs-e\s*(\d{1,3})|competência da nfs-e\s*(\d{1,3})(?![/\d])|emissão da nfs-e\s*(\d{1,3})(?![/\d])'        
        patternValueGovFederal = r'r\$ \d{1,3}\.\d{1,3},\d{2}|r\$ \d{1,3},\d{2}'
        patternCodServGovFederal = patternCodServPmrj
        patternDocNfGovFederal = r'cnpj / cpf / nif\s*\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'

        patternValue = patternValuePmsp + '|' + patternValuePmrj + '|' + patternValueGovFederal
        patternDate = patternDatePmsp + '|' + patternDatePmrj + '|' + patternDateGovFederal
        patternNumberNf = patternNumberNfPmsp + '|' + patternNumberNfPmrj + '|' + patternNumberNfGovFederal
        patternCodServ = patternCodServPmsp + '|' + patternCodServPmrj + '|' + patternCodServGovFederal
        patternDocNf = patternDocNfPmsp + '|' + patternDocNfPmrj + '|' + patternDocNfGovFederal
        
        
        for docNf in re.finditer(patternDocNf, st.session_state.txtOcr):
            st.session_state.docNfOcr = docNf.group(0).replace('nif', '').replace('cpf', '').replace('cnpj', '').replace('-', '').replace(':', '').replace('/', '').replace('.', '').replace(' ', '').replace('\n','').replace('\t','')
            listDocNf.append(st.session_state.docNfOcr)
        if len(listDocNf) > 1 and isinstance(listDocNf,list):  
            st.session_state.docNfOcr = listDocNf

        for codServ in re.finditer(patternCodServ, st.session_state.txtOcr):
            st.session_state.codServOcr = codServ.group(0)
            listCodServ.append(st.session_state.codServOcr)
        if len(listCodServ) != 0: 
            st.session_state.codServOcr = listCodServ[0].replace('serviço', '').replace('-', '').replace(' ', '').replace('\n','').replace('\t','')

        st.session_state.numberNfOcr = re.findall(patternNumberNf, st.session_state.txtOcr)
        if len(st.session_state.numberNfOcr) > 0:
            listNumberNf = [item for tupla in st.session_state.numberNfOcr for item in tupla if item != '' and  item != ' ']     
            listNumberNf.sort(reverse = True) 
            st.session_state.numberNfOcr = nfTrata(str(listNumberNf[0]))

        st.session_state.dtEmissaoOcr = re.findall(patternDate, st.session_state.txtOcr)
        if len(st.session_state.dtEmissaoOcr) > 0 :
            listDate = [item for tupla in st.session_state.dtEmissaoOcr for item in tupla if item != '' and  item != ' ']     
            listDate.sort(reverse = True) 
            st.session_state.dtEmissaoOcr = listDate[0]

        for value in re.finditer(patternValue, st.session_state.txtOcr):
            st.session_state.valueDocOcr = value.group(0).lower()
            if len(st.session_state.valueDocOcr) > 2:
                st.session_state.valueDocOcr = st.session_state.valueDocOcr.replace('=','').replace('.','').replace(',', '').replace('=','').replace('r$','').replace('do','').replace('serviço','').replace('valor','').replace('total','').replace('da','').replace('nota','').replace('\t','').replace(' ','').replace('\n','')
                st.session_state.valueDocOcr = st.session_state.valueDocOcr[:-2] + '.' + st.session_state.valueDocOcr[-2:] 
                listValue.append(float(st.session_state.valueDocOcr))
                listValue.sort(reverse= True)
                if len(listValue) > 0:
                    st.session_state.valueDocOcr = listValue[0]

        st.write(f'st.session_state.codServOcr: {st.session_state.codServOcr}')
        st.write(f'st.session_state.numberNfOcr: {st.session_state.numberNfOcr}')
        st.write(f'st.session_state.dtEmissaoOcr: {st.session_state.dtEmissaoOcr}')
        st.write(f'st.session_state.docNfOcr: {st.session_state.docNfOcr}')
        st.write(f'st.session_state.valueDocOcr: {st.session_state.valueDocOcr}')

                
                
st.session_state.arquivoObject = ''             
st.session_state.arquivoObject = st.file_uploader(f'inclua o anexo', type =['.pdf', '.jpg', '.jpge', '.png'])

if (st.session_state.arquivoObject == None) or st.session_state.arquivoObject == '':
    st.warning("Atenção! Faça o Upload do arquivo.", icon="🚨")
    st.stop()
else:
        
    st.session_state.arquivoObjectToOcr = st.session_state.arquivoObject
    startMediumPointOcr()
    st.stop()


