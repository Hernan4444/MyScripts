from requests import Session
from apiclient.http import MediaFileUpload
from io import BytesIO
from os.path import exists
from googleapiclient.http import MediaIoBaseDownload
from oauth2client.file import Storage
from oauth2client import tools, client
from oauth2client.client import AccessTokenCredentials
from googleapiclient.discovery import build
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from json import load as json_load
from shutil import copyfileobj

SCOPES = ["https://www.googleapis.com/auth/drive"]

# Private functions to authenticate
def _refresh_access_token(cred_name):
    with open(cred_name) as file:
        creds = json_load(file)

    client_id = creds["client_id"]
    client_secret = creds["client_secret"]
    refresh_token = creds["token_response"]["refresh_token"]
    request = Request(
        "https://accounts.google.com/o/oauth2/token",
        data=urlencode(
            {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            }
        ).encode(),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )

    response = json.load(urlopen(request))
    return response["access_token"]


def _get_credentials(cred_name):
    if not exists(cred_name):
        return None

    user_agent = "Google Drive API for Python"
    access_token = _refresh_access_token(cred_name)
    revoke_uri = "https://accounts.google.com/o/oauth2/revoke"
    creds = AccessTokenCredentials(
        access_token=access_token, user_agent=user_agent, revoke_uri=revoke_uri
    )
    return creds


def _authenticate(cred_name="cred.json", client_secret_name="credentials.json"):
    store = Storage(cred_name)
    creds = store.get()
    if not creds or creds.invalid:
        creds = _get_credentials(cred_name)

        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(client_secret_name, SCOPES)
            creds = tools.run_flow(flow, store)

    return creds


def _get_service():
    creds = _authenticate()
    return build("drive", "v3", credentials=creds)


# Public functions
def folder_list(folder_id):
    service = _get_service()
    gdrive = service.files()
    res = gdrive.list(
        q="'%s' in parents" % folder_id,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        corpora="allDrives",
    ).execute()
    return res["files"]


def folder_download(folder_id):
    for fid in folder_list(folder_id):
        download_file_from_google_drive(fid["id"], fid["name"])


def folder_download_by_name_and_parent_id(parent_id, folder):
    print("Bajar archivos de la carpeta '{}'".format(folder))
    for folder_data in folder_list(folder_id):
        if folder_data["name"] != folder:
            continue

        folder_download(folder_data["id"])


def download_file_from_google_drive(id, destination):
    service = _get_service()
    print("\tDownload {}".format(destination))
    request = service.files().get_media(fileId=id)

    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    # The file has been downloaded into RAM, now save it in a file
    fh.seek(0)
    with open(destination, "wb") as f:
        copyfileobj(fh, f, length=131072)

    return


def download_file_without_authenticate(id, destination):
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith("download_warning"):
                return value

    URL = "https://docs.google.com/uc?export=download"
    session = Session()
    response = session.get(URL, params={"id": id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {"id": id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for i, chunk in enumerate(response.iter_content(CHUNK_SIZE)):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

    return None


# Subir un archivo a una carpeta
def upload_file_to_folder(path_file, name_file, folder_id=None, delete_same_name=True):
    service = _get_service()
    media = MediaFileUpload(path_file)
    body = {
        "name": name_file,
    }
    if folder_id is not None:
        body["parents"] = [folder_id]

        if delete_same_name:
            for fid in folder_list(folder_id):
                if fid["name"] != name_file:
                    service.files().delete(
                        fileId=fid["id"], supportsAllDrives=True
                    ).execute()

    file = (
        service.files()
        .create(media_body=media, body=body, supportsAllDrives=True)
        .execute()
    )
    return file["id"]


def create_folder(folder, parents=None):
    service = _get_service()
    file_metadata = {
        "name": folder,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parents:
        file_metadata["parents"] = [IDS["classified"]]
    file = (
        service.files()
        .create(body=file_metadata, fields="id", supportsAllDrives=True)
        .execute()
    )

    return file["id"]


if __name__ == "__main__":
    download_file_without_authenticate("13ZJCu96cbGowI-lGIrQuqiyUTw7azqLb", "game.mp4")

    for x in folder_list("1gVNbRdUha4QPrASjgBRZBEoTUebl6f4W"):
        print(x)

    folder_download("1gVNbRdUha4QPrASjgBRZBEoTUebl6f4W")

