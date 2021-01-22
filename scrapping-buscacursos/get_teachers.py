from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime, timedelta
import os
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
import json
from selenium.webdriver.common.keys import Keys
import shutil
from datetime import datetime   
import sys
import pymongo

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

IGNORE = ["BIO143M-1", "BIO141C-5"]

def get_text(element):
    text = element.text.strip()
    if "-" in text:
        return text.split("-")[1].strip()
    return text


def get_teacher(element):
    teachers = []
    for x in element.find_elements_by_tag_name('a'):
        teachers.append(x.text.strip())
    if len(teachers):
        return ", ".join(teachers)
    return "(Sin Profesores)"


def get_courses(driver, year, semester, initials):
    link = "http://buscacursos.uc.cl/?cxml_semestre={}-{}&cxml_sigla={}&cxml_nrc=&cxml_nombre=&cxml_categoria=TODOS&cxml_profesor=&cxml_campus=TODOS&cxml_unidad_academica=TODOS&cxml_horario_tipo_busqueda=si_tenga&cxml_horario_tipo_busqueda_actividad=TODOS#resultados"
    driver.get(link.format(year, semester, initials))
    inputElement = driver.find_elements_by_xpath("//a[starts-with(@onclick,'javascript:test(')]")

    data = []

    for grade in inputElement:
        teacher = grade.find_element_by_xpath('../..').find_elements_by_tag_name('td')[10]
        teacher = get_teacher(teacher)
        grade.send_keys(Keys.RETURN)
        time.sleep(0.5)

        div = driver.find_element_by_id('div1')
        tds = div.find_elements_by_tag_name('tr')
        initials = tds[2].find_elements_by_tag_name('td')[-1].text.strip()
        
        if initials in IGNORE: 
            driver.find_element_by_id('btnClose').click()
            time.sleep(0.5)
            continue

        print([name, initials, teacher])
        data.append([initials, teacher])

        # driver.find_element_by_id('btnClose').send_keys(Keys.RETURN)
        driver.find_element_by_id('btnClose').click()
        time.sleep(0.5)
        
    return data


def scrap_buscacurso(year, semester):
    if 'GOOGLE_CHROME_BIN' in os.environ: # Heroku
        GOOGLE_CHROME_BIN = os.environ['GOOGLE_CHROME_BIN']
    else: # Local
        GOOGLE_CHROME_BIN = os.path.join(
            "/", "Applications", "Google Chrome.app", "Contents", "MacOS", "Google Chrome")

    if 'CHROME_DRIVER' in os.environ: # Heroku
        CHROME_DRIVER = os.environ['CHROME_DRIVER']
    else:
        CHROME_DRIVER = os.path.join('/', 'Library', 'chromedriver')

    options = Options()
    if 'GOOGLE_CHROME_BIN' in os.environ:
        options.add_argument("--headless")
        options.binary_location = GOOGLE_CHROME_BIN

    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    if 'GOOGLE_CHROME_BIN' in os.environ: # Heroku
        driver = webdriver.Chrome(executable_path=CHROME_DRIVER, options=options)
        actual_time = datetime.now() - timedelta(hours=4)
    else: # Local
        driver = webdriver.Safari()
        actual_time = datetime.now()


    print(actual_time)
    data_courses = []
    CURSOS = ["IIC1", "IIC2", "IIC3", "ICH1104", "BIO110C", "BIO141C", "BIO135C", "BIO143M", "EYP2114", "ICS2", "ICS3"]
    for initials in CURSOS:
        data_courses.extend(get_courses(driver, year, semester, initials))

    data_courses = pd.DataFrame(data_courses)    
    driver.close()
    return data_courses

if __name__ == "__main__":
    year = 2020
    semester = 1

    data = scrap_buscacurso(year, semester)

    TEACHERS = {}
    for _, x in data.iterrows():
        sigle_section teacher = x
        TEACHERS[sigle_section] = teacher
        
    with open(f"TEACHER-{year}-{semester}.json", "w") as file:
        json.dump(TEACHERS, file, ensure_ascii=False)

    