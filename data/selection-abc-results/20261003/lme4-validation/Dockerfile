FROM mcr.microsoft.com/playwright:v1.58.2-noble
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends r-base-core r-cran-lme4 && rm -rf /var/lib/apt/lists/*
WORKDIR /evidence
