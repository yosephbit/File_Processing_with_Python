FROM python:3.10-slim-buster as base

# TARGETARCH is provided automatically by the builder, but you have to opt into it
# https://docs.docker.com/engine/reference/builder/#automatic-platform-args-in-the-global-scope
ARG TARGETARCH
RUN echo "@@@@@@ TARGETARCH IS ... `${TARGETARCH}` @@@@@@"
ARG WKHTMLTOPDF_VERSION=0.12.6-1

RUN apt-get autoclean && \ 
 apt-get autoremove && \ 
 apt-get -f install && \ 
 apt-get dist-upgrade

# Install wkhtmltopdf
RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install --no-install-recommends -y \
	\
	# necessary for downloading wkhtmltopdf
	curl \
	\
	# we use this to convert office docs to pdf
	libreoffice \
	\
	# libreoffice complains if no JVM running
	default-jre \
	# \
	# # uncomment for stress testing
	# htop \
	\
	# we need `gcc` to install psutil
	build-essential \
	wkhtmltopdf

# RUN curl -fsL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb > /tmp/wkhtmltopdf.deb
# RUN curl -fsL https://github.com/wkhtmltopdf/packaging/releases/download/${WKHTMLTOPDF_VERSION}/wkhtmltox_${WKHTMLTOPDF_VERSION}.buster_${TARGETARCH}.deb > /tmp/wkhtmltopdf.deb
# RUN dpkg -i /tmp/wkhtmltopdf.deb

ENV \
	# misc
	SHELL=/bin/bash \
	\
	# python
	PYTHONFAULTHANDLER=1 \
	PYTHONHASHSEED=random \
	\
	# pip
	PIP_NO_CACHE_DIR=off \
	PIP_DISABLE_PIP_VERSION_CHECK=on \
	PIP_DEFAULT_TIMEOUT=500 \
	\
	# poetry
	POETRY_VERSION=1.1.12 \
	# find binaries in poetry bin and local python bin directories
	PATH="/home/fastapi/.poetry/bin:/home/fastapi/.local/bin:$PATH"

# create fastapi user with home dir
RUN useradd -m fastapi -d /home/fastapi --shell /bin/bash
# become fastapi user for the rest of the build
USER fastapi
# here's where the source code + app goes
WORKDIR /home/fastapi/app

# copy over the dependency files (we'll copy code later)
COPY pyproject.toml poetry.lock ./

# install poetry - respects $POETRY_VERSION
RUN curl -sSL https://install.python-poetry.org | python


EXPOSE 8080

FROM base as dev

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy remaining files
COPY . .

RUN echo "Building with uvicorn and live reload ..."
CMD [ \
	"poetry", \
	"run", \
	"uvicorn", \
	"processing_tools.main:app", \
	"--host", \
	"0.0.0.0", \
	"--port", \
	"8080", \
	"--reload" \
]

FROM base

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# Copy remaining files
COPY . .


ARG GIT_SHA
ENV GIT_SHA=${GIT_SHA}

RUN echo "Building with gunicorn ..."
CMD [ \
	"gunicorn", \
	"processing_tools.main:app", \
	\
	# use file config - see file for details
	"--log-config", \
	"processing_tools/logging/logging.conf", \
	\
	# only one worker
	"--workers", \
	"1", \
	\
	# two minutes before timeout
	"--graceful-timeout", \
	"120", \
	\
	"--worker-class", \
	"uvicorn.workers.UvicornWorker", \
	\
	# allow 2 minutes before timing out
	"--timeout", \
	"120", \
	\
	"--bind", \
	"0.0.0.0:8080" \
]
