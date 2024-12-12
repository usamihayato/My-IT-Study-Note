FROM containerregistryakspoc.azurecr.io/aks-env-base:20220207-beta

COPY . /usr/src/app/batch
WORKDIR /usr/src/app/batch

CMD ["python", "app.py", "--disable_force_cleanup", "--disable_override_base_path"]
