ARG registry=acrprivatepocje001
ARG base_tag=v2.4.6

FROM  ${registry}.azurecr.io/openapi/aks-env-base:${base_tag}

USER dmadmin

WORKDIR /usr/src/app
COPY --chown=dmadmin:dmadmin src/app/ .
ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"

CMD ["uwsgi", "--ini", "./uwsgi.ini"]
