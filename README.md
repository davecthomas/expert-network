## Expert Network
A working analysis of the practicality of indexing topic experts.

## Installation
Create an isolated Python environment in a directory external to your project and activate it:
```
python3 -m venv env
source env/bin/activate
```
Navigate to your project directory and install dependencies:
```
cd YOUR_PROJECT
pip3 install  -r requirements.txt
```
### Prep for use of Google Cloud
1. Create a Google Cloud Project and get the ID
2. Create and download a service account credential from Google (https://cloud.google.com/firestore/docs/quickstart-servers)
3. Set GCLOUD_PROJECT environment variable
```
export GOOGLE_APPLICATION_CREDENTIALS=/Users/<you>/expert-network-service-account.json
export GCLOUD_PROJECT=expert-network-262703
```
## Run It
Launch by a command:
```
flask run
```
The daemon should start and you can access it's web interface at 127.0.0.1 

## Admin tasks
```
flask admin import_sites
flask admin import_experts
```

## Avoid Google Cloud costs in test mode
To prevent document writes or deletes...
