from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime, timedelta
import os
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from selenium.webdriver.common.keys import Keys
import shutil
from datetime import datetime   
import sys
import pymongo


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


def get_text(element):
    text = element.text.strip()
    if "-" in text:
        return text.split("-")[1].strip()
    return text


def get_courses(driver, year, semester, initials):
    link = "http://buscacursos.uc.cl/?cxml_semestre={}-{}&cxml_sigla={}&cxml_nrc=&cxml_nombre=&cxml_categoria=TODOS&cxml_profesor=&cxml_campus=TODOS&cxml_unidad_academica=TODOS&cxml_horario_tipo_busqueda=si_tenga&cxml_horario_tipo_busqueda_actividad=TODOS#resultados"
    driver.get(link.format(year, semester, initials))
    inputElement = driver.find_elements_by_xpath("//a[starts-with(@onclick,'javascript:test(')]")

    data = []

    for grade in inputElement:
        teacher = grade.find_element_by_xpath('../..').find_elements_by_tag_name('td')[10]
        teacher = teacher.find_element_by_tag_name('a').text.strip()
        grade.send_keys(Keys.RETURN)
        time.sleep(1)

        div = driver.find_element_by_id('div1')
        tds = div.find_elements_by_tag_name('tr')
        name = get_text(tds[2].find_elements_by_tag_name('td')[0])
        initials = tds[2].find_elements_by_tag_name('td')[-1].text.strip()

        for tr in tds[4: len(tds) - 2]:
            columns = tr.find_elements_by_tag_name('td')
            type_vacant = get_text(columns[0])
            offer_vacant = int(get_text(columns[-3]))
            available_vacant = int(get_text(columns[-1]))
            print([name, initials, type_vacant, offer_vacant, teacher, available_vacant])

            data.append([name, initials, type_vacant, offer_vacant, teacher, available_vacant])


        # driver.find_element_by_id('btnClose').send_keys(Keys.RETURN)
        driver.find_element_by_id('btnClose').click()
        time.sleep(1)
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
    for initials in ["IIC1", "IIC2", "IIC3"]:
        data_courses.extend(get_courses(driver, year, semester, initials))

    data_courses = pd.DataFrame(data_courses)    
    driver.close()
    return data_courses


# DEPRECATED FUNCTION
def update():
    if os.path.exists('visualization-files'):
        shutil.rmtree('visualization-files')

    os.system("git clone https://github.com/Hernan4444/visualization-files")
    shutil.copyfile("token.pickle", os.path.join("visualization-files", "token.pickle") )
    os.chdir("visualization-files/")
    os.system("python3 update.py {} {} github.com/Hernan4444/visualization-files".format(USER, PASSWORD))
    os.chdir("../")
    shutil.rmtree('visualization-files')


def update_mongodb(year, semester):
    client = pymongo.MongoClient(os.environ["MONGO_URL"])
    banner = client.Banner.Banner
    translate_document = banner.find_one({"NAME": "INITIALS-TO-NAME"})
    course_document = get_course_document(year, semester, banner)

    data = scrap_buscacurso(year, semester)
    #data = pd.read_csv("temporal_data.csv", encoding="UTF-8")

    if 'GOOGLE_CHROME_BIN' in os.environ: # Heroku
        actual_time = datetime.now() - timedelta(hours=4)
    else: # Local
        actual_time = datetime.now()

    # Falta Actualizar profesor
    actual_course = None
    updated_translate_document = False
    for _, x in data.iterrows():
        name, sigle_section, type_vacant, offer_vacant, teacher, available_vacant = x
        if actual_course is None:
            actual_course = sigle_section

        if actual_course != sigle_section:  # Calcular el total de cupos disponibles
            total = 0
            for type_ in course_document["COURSES"][actual_course]["TYPES"]:
                total += course_document["COURSES"][actual_course]["TYPES"][type_]["AVAILABLE"][-1]
            course_document["COURSES"][actual_course]["TOTAL"].append(total)

            actual_course = sigle_section
        
        initials, section = sigle_section.split("-")
        if initials not in translate_document:
            updated_translate_document = True
            translate_document[initials] = name

        
        if sigle_section not in course_document["COURSES"]:
            course_document["COURSES"][sigle_section] = {
                "TOTAL": [],
                "TYPES": {},
                "INDEXTIMESTAMPS": len(course_document["TIMESTAMPS"]),
                "TEACHER": teacher
            }

        if type_vacant not in course_document["COURSES"][sigle_section]["TYPES"]:
            course_document["COURSES"][sigle_section]["TYPES"][type_vacant] = {
                "AVAILABLE": [],
                "OFFER": []
            }
        
        course_document["COURSES"][sigle_section]["TYPES"][type_vacant]["AVAILABLE"].append(available_vacant)

        if len(course_document["COURSES"][sigle_section]["TYPES"][type_vacant]["OFFER"]) == 0:
            course_document["COURSES"][sigle_section]["TYPES"][type_vacant]["OFFER"].append([str(actual_time), offer_vacant])

        if course_document["COURSES"][sigle_section]["TYPES"][type_vacant]["OFFER"][-1][1] != offer_vacant:
            past_time = actual_time - timedelta(minutes=5)
            past_offer = course_document["COURSES"][sigle_section]["TYPES"][type_vacant]["OFFER"][-1][1]
            course_document["COURSES"][sigle_section]["TYPES"][type_vacant]["OFFER"].append([str(past_time), past_offer])
            course_document["COURSES"][sigle_section]["TYPES"][type_vacant]["OFFER"].append([str(actual_time), offer_vacant])

    course_document["TIMESTAMPS"].append(str(actual_time))

    if updated_translate_document:
        update_document(banner, {"NAME": "INITIALS-TO-NAME"}, translate_document)

    update_document(banner, {"NAME": "COURSES", "SEMESTER": semester, "YEAR": year}, course_document)


def get_course_document(year, semester, banner):
    course_document = banner.find_one({"NAME": "COURSES", "SEMESTER": semester, "YEAR": year})
    if course_document is None:
        course_document = {
            "NAME": "COURSES",
            "SEMESTER": semester,
            "YEAR": year,
            "TIMESTAMPS": [],
            "COURSES": {}
            }
    return course_document


def update_document(banner, filter, new_document):
    banner.replace_one(filter, new_document, upsert=True)


if __name__ == "__main__":
    if 'GOOGLE_CHROME_BIN' in os.environ: # Heroku
        actual_time = datetime.now() - timedelta(hours=4)
    else: # Local
        actual_time = datetime.now()

    date_start, date_end = os.environ["DATES"].split(";")
    time_start, time_end = os.environ["TIMES"].split(";")
    year = int(os.environ["YEAR"])
    semester = int(os.environ["SEMESTER"])

    date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
    date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
    time_start = datetime.strptime(time_start, '%H:%M').time()
    time_end = datetime.strptime(time_end, '%H:%M').time()
    

    can_update_mongodb = True
    if actual_time.date() < date_start or date_end < actual_time.date():
        can_update_mongodb = False
        
    elif actual_time.time() < time_start or time_end < actual_time.time():
        can_update_mongodb = False

    # Solo si hago python3 main.py --force o estoy dentro del rango posible, se ejecuta la función
    if (len(sys.argv) > 1 and sys.argv[1] == "--force") or can_update_mongodb :
        update_mongodb(year, semester)
    else:
        print(f"Script solo se ejecuta entre los días {date_start} y {date_end}, y entre las {time_start} y {time_end}")
