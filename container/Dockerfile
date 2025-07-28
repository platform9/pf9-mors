FROM  artifactory.platform9.horse/docker-local/pf9-py39-baseimg-alpine:pcd-graviton-v4
LABEL com.platform9.image-type=du
ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache

RUN apk update && \
    apk add \
    bash 

RUN apk add pkgconfig
RUN apk add mariadb \
     mariadb-client \
     --no-cache mariadb-dev \
     mariadb-connector-c-dev \
     python3-dev

RUN python -m ensurepip --upgrade

WORKDIR /root
COPY etc/ /etc/
COPY mors-sdist.tgz \
     requirements.txt \
     /root/

RUN mkdir -p /opt/pf9/pf9-mors/bin/
RUN mkdir -p /var/log/pf9
RUN mkdir -p /etc/pf9
COPY pf9_mors.py /opt/pf9/pf9-mors/bin/pf9_mors.py
COPY mors_manage.py /opt/pf9/pf9-mors/bin/mors_manage.py
COPY migrate.cfg /usr/local/lib/python3.9/site-packages/mors_repo/
COPY init-region .

RUN chmod 755 init-region


RUN pip install mors-sdist.tgz -r requirements.txt

EXPOSE 8989
CMD \
    supervisord -c /etc/supervisord.conf

ARG VERSION
LABEL com.platform9.pf9_version=${VERSION}
ARG BUILD_ID
LABEL com.platform9.build=${BUILD_ID}
LABEL com.platform9.version="${VERSION}-${BUILD_ID}"
ARG BRANCH
LABEL com.platform9.branch=${BRANCH}
ARG APP_METADATA
LABEL com.platform9.app_metadata=${APP_METADATA}
