# Scrapping con selenium en heroku

Script para poder hacer scrapping de buscacurso y guardar los datos en mongodb.

## Buildpacks

Agregar (en orden) los siguientes buildpacks para ejecutarlo en Heroku.

1. heroku/python
2. https://buildpack-registry.s3.amazonaws.com/buildpacks/heroku/chromedriver.tgz
3. https://buildpack-registry.s3.amazonaws.com/buildpacks/heroku/google-chrome.tgz

## Variables de entorno

* `DATES`: Rango de horas donde se guarda la info. Deben estar separadas con un `;` y el formato es **AÑO-MES-DÍA**. Por ejemplo `2020-07-19;2020-07-19`.

* `TIMES`: Rango de horas donde se guarda la info. Deben estar separadas con un `;`. Por ejemplo `08:00;22:00`.

* `YEAR`: Año al cual aplicar el scrapping.

* `SEMESTER`: Semestre al cual aplicar el scrapping.

* `MONGO_URL`: Link al mongodb (con todo seteado como usuario y contraseña).

* `CHROME_DRIVER`: Path del chrome driver. En heroku es **/app/.chromedriver/bin/chromedriver**.

* `GOOGLE_CHROME_BIN`: Path del chrome bin. En heroku es **/app/.apt/usr/bin/google-chrome**.