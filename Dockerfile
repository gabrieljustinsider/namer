FROM python:3.11-slim AS base

ENV TZ=Europe/London
ARG DEBIAN_FRONTEND=noninteractive

# Install dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
       tzdata \
       curl \
       pipx \
    && rm -rf /var/lib/apt/lists/* \
    && rm -Rf /usr/share/doc && rm -Rf /usr/share/man \
    && apt-get clean

FROM base AS build
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libffi-dev \
       libssl-dev \
       wget \
       git \
       npm \
    && rm -rf /var/lib/apt/lists/* \
    && rm -Rf /usr/share/doc && rm -Rf /usr/share/man \
    && apt-get clean

RUN pip install --upgrade pip setuptools wheel poetry

RUN mkdir /work/
COPY . /work
WORKDIR /work
RUN rm -rf /work/namer/__pycache__/ || true \
    && rm -rf /work/test/__pycache__/ || true \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi
RUN npm install -g pnpm && pnpm install && pnpm run build
RUN poetry build

FROM base
COPY --from=build /work/dist/namer-*.tar.gz /
RUN pip install /namer-*.tar.gz \
    && rm /namer-*.tar.gz

ARG BUILD_DATE
ARG GIT_HASH
ARG PROJECT_VERSION

ENV PYTHONUNBUFFERED=1
ENV NAMER_CONFIG=/config/namer.cfg
ENV BUILD_DATE=$BUILD_DATE
ENV GIT_HASH=$GIT_HASH
ENV PROJECT_VERSION=$PROJECT_VERSION

EXPOSE 6980
HEALTHCHECK --interval=1m --timeout=30s CMD curl -s $(namer url)/api/healthcheck >/dev/null || exit 1
ENTRYPOINT ["namer", "watchdog"]

FROM base
ENV PATH="/root/.local/bin:$PATH"
COPY --from=build /work/dist/namer-*.tar.gz /
RUN pipx install /namer-*.tar.gz \
    && rm /namer-*.tar.gz

ARG BUILD_DATE
ARG GIT_HASH
ARG PROJECT_VERSION

ENV PYTHONUNBUFFERED=1
ENV NAMER_CONFIG=/config/namer.cfg
ENV BUILD_DATE=$BUILD_DATE
ENV GIT_HASH=$GIT_HASH
ENV PROJECT_VERSION=$PROJECT_VERSION

EXPOSE 6980
HEALTHCHECK --interval=1m --timeout=30s CMD curl -s $(namer url)/api/healthcheck >/dev/null || exit 1
ENTRYPOINT ["namer", "watchdog"]
