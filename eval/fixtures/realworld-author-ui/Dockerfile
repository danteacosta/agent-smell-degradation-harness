FROM mcr.microsoft.com/playwright:v1.58.2-noble@sha256:6446946a1d9fd62d9ae501312a2d76a43ee688542b21622056a372959b65d63d
WORKDIR /opt/realworld-author-ui
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --omit=dev --no-audit --no-fund && npm cache clean --force
COPY runner.cjs ./runner.cjs
ENV HOME=/tmp
USER pwuser
ENTRYPOINT ["node", "/opt/realworld-author-ui/runner.cjs"]
