# Google Drive Script

Código usado para realizar ciertas acciones en google drive. En particular, se encuentran funciones para:

- Ver el contenido de una carpeta de drive
- Subir un archivo
- Descargar un archivo
- Descargar un archivo público sin necesidad de auntentificar

## Funciones disponibles

- `folder_list(folder_id)`: retorna una lista con todos los archivos de la carpeta en drive con ID = `folder_id`.

- `folder_download(folder_id)`: descarga todos los archivos de la carpeta en drive con ID = `folder_id`.

- `folder_download_by_name_and_parent_id(parent_id, folder)`: descarga todos los archivos de la carpeta en drive con nombre = `folder` y que esté dentro de la carpeta en drive con ID = `parent_id`.

- `download_file_from_google_drive(id, destination)`: descarga el archivo con id = `id` y lo guarda según el path indicado en `destination`.

- `download_file_without_authenticate(id, destination)`: descarga un archhivo público con id = `id` y lo guarda según el path indicado en `destination`. Esta función no requiere auntentificación para su ejecución.

- `upload_file_to_folder(path_file, name_file, folder_id=None, delete_same_name=True)`: sube un archivo cuyo path se indica en `path_file` y lo sube con el nombre indicado en `name_file`. Este se sube dentro de la carpeta en drive con ID = `folder_id`. En caso que `delete_same_name` es `True`, entonces se elimina cualquier archivo que se llame exactamente igual al archivo a subir.

- `create_folder(folder, parents=None)`: crea una carpeta cuyo nombre se indica en `folder` dentro de una carpeta en drive con ID = `parents`. En caso de no entregar `parents`, la carpeta se crea en la raíz el drive.

## Autentificación

Para poder autentificar la cuenta, primero es necesario disponer de un archivo llamado `credentials.json` que lo pueden descargar de la siguiente página: https://developers.google.com/drive/api/v3/quickstart/python#step_1_turn_on_the. Luego, el código de forma interna va a utilizar ese archivo, solicitará hacer login desde el browser y creará un archivo llamado `cred.json` que permitirá a las funciones anteriores funcionar sin ninguna dificultad.