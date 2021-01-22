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

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

DELTA = int(os.environ["DELTA"])


def get_text(element):
    text = element.text.strip()
    if "-" in text:
        return text.split("-")[1].strip()
    return text


def get_teacher(element):
    teachers = []
    for x in element.find_elements_by_tag_name("a"):
        teachers.append(x.text.strip())
    if len(teachers):
        return ", ".join(teachers)
    return "(Sin Profesores)"


def get_courses(driver, year, semester, initials):
    link = "http://buscacursos.uc.cl/?cxml_semestre={}-{}&cxml_sigla={}&cxml_nrc=&cxml_nombre=&cxml_categoria=TODOS&cxml_profesor=&cxml_campus=TODOS&cxml_unidad_academica=TODOS&cxml_horario_tipo_busqueda=si_tenga&cxml_horario_tipo_busqueda_actividad=TODOS#resultados"
    driver.get(link.format(year, semester, initials))
    inputElement = driver.find_elements_by_xpath(
        "//a[starts-with(@onclick,'javascript:test(')]"
    )

    data = []

    for grade in inputElement:
        teacher = grade.find_element_by_xpath("../..").find_elements_by_tag_name("td")[
            10
        ]
        teacher = get_teacher(teacher)
        grade.send_keys(Keys.RETURN)
        time.sleep(0.5)

        div = driver.find_element_by_id("div1")
        tds = div.find_elements_by_tag_name("tr")
        name = get_text(tds[2].find_elements_by_tag_name("td")[0])
        initials = tds[2].find_elements_by_tag_name("td")[-1].text.strip()


        for tr in tds[4 : len(tds) - 2]:
            columns = tr.find_elements_by_tag_name("td")
            type_vacant = []
            for i in range(6):
                type_vacant_text = get_text(columns[i])
                if len(type_vacant_text.replace(" ", "")) != 0:
                    type_vacant.append(type_vacant_text.strip())

            type_vacant = "-".join(type_vacant)
            offer_vacant = int(get_text(columns[-3]))
            available_vacant = int(get_text(columns[-1]))
            print([initials, type_vacant, offer_vacant, available_vacant])
            data.append(
                [name, teacher, initials, type_vacant, offer_vacant, available_vacant]
            )

        driver.find_element_by_id("btnClose").click()
        time.sleep(0.5)
    return data


def scrap_buscacurso(year, semester):
    if "GOOGLE_CHROME_BIN" in os.environ:  # Heroku
        GOOGLE_CHROME_BIN = os.environ["GOOGLE_CHROME_BIN"]
    else:  # Local
        GOOGLE_CHROME_BIN = os.path.join(
            "/",
            "Applications",
            "Google Chrome.app",
            "Contents",
            "MacOS",
            "Google Chrome",
        )

    if "CHROME_DRIVER" in os.environ:  # Heroku
        CHROME_DRIVER = os.environ["CHROME_DRIVER"]
    else:
        CHROME_DRIVER = os.path.join("/", "Library", "chromedriver")

    options = Options()
    if "GOOGLE_CHROME_BIN" in os.environ:
        options.add_argument("--headless")
        options.binary_location = GOOGLE_CHROME_BIN

    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    if "GOOGLE_CHROME_BIN" in os.environ:  # Heroku
        driver = webdriver.Chrome(executable_path=CHROME_DRIVER, options=options)
    else:  # Local
        driver = webdriver.Safari()

    data_courses = []
    CURSOS = [
        "IIC1",
        "IIC2",
        "IIC3",
        "ICH1104",
        "BIO110C",
        "BIO141C",
        "BIO135C",
        "BIO143M",
        "EYP2114",
        "ICS2",
        "ICS3",
    ]
    for initials in CURSOS:
        data_courses.extend(get_courses(driver, year, semester, initials))

    driver.close()
    return data_courses


def update_mongodb(year, semester, actual_time):
    client = pymongo.MongoClient(os.environ["MONGO_URL"])
    database = client.Banner

    sigle_collection = database.sigles
    course_colection = database["{}-{}".format(year, semester)]

    translate_document = sigle_collection.find_one({"NAME": "INITIALS-TO-NAME"})
    teachers_document = get_teacher_document(course_colection)

    if translate_document is None:
        translate_document = {"NAME": "INITIALS-TO-NAME"}

    data = scrap_buscacurso(year, semester)

    course_document = {
        "DATE": str(actual_time),
        "COURSES": [x[2:] for x in data],
    }

    updated_translate_document = False
    for name, teacher, sigle_section, _, _, _ in data:
        initials, section = sigle_section.split("-")
        if initials not in translate_document:
            updated_translate_document = True
            translate_document[initials] = name

        teachers_document["COURSES"][sigle_section] = teacher

    if updated_translate_document:
        update_document(
            sigle_collection, {"NAME": "INITIALS-TO-NAME"}, translate_document
        )

    update_document(
        course_colection,
        {"NAME": "TEACHERS"},
        teachers_document,
    )
    add_document(course_colection, course_document)


def get_teacher_document(collection):
    teacher_document = collection.find_one({"NAME": "TEACHERS"})
    if teacher_document is None:
        teacher_document = {
            "NAME": "TEACHERS",
            "COURSES": {},
        }
    return teacher_document


def add_document(collection, new_document):
    collection.insert_one(new_document)


def update_document(collection, filter_, new_document):
    collection.replace_one(filter_, new_document, upsert=True)


if __name__ == "__main__":
    start_time = time.time()
    if "GOOGLE_CHROME_BIN" in os.environ:  # Heroku
        actual_time = datetime.now() - timedelta(hours=DELTA)
    else:  # Local
        actual_time = datetime.now()

    date_start, date_end = os.environ["DATES"].split(";")
    time_start, time_end = os.environ["TIMES"].split(";")
    year = int(os.environ["YEAR"])
    semester = int(os.environ["SEMESTER"])

    date_start = datetime.strptime(date_start, "%Y-%m-%d").date()
    date_end = datetime.strptime(date_end, "%Y-%m-%d").date()
    time_start = datetime.strptime(time_start, "%H:%M").time()
    time_end = datetime.strptime(time_end, "%H:%M").time()

    can_update_mongodb = True
    if actual_time.date() < date_start or date_end < actual_time.date():
        can_update_mongodb = False

    elif actual_time.time() < time_start or time_end < actual_time.time():
        can_update_mongodb = False

    # Solo si hago python3 main.py --force o estoy dentro del rango posible, se ejecuta la función
    if (len(sys.argv) > 1 and sys.argv[1] == "--force") or can_update_mongodb:
        update_mongodb(year, semester, actual_time)
    else:
        print(actual_time)
        print(
            f"Script solo se ejecuta entre los días {date_start} y {date_end}, y entre las {time_start} y {time_end}"
        )

    print(f"operación realizada en {round(time.time() - start_time)} seg")