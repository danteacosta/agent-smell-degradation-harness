FROM cypress/included:15.14.2@sha256:9f27bf8330595fe44dc3ba9c0c96cff1618d24241bd9f95a470f8f6e2ecfba7e
ENV CYPRESS_CACHE_FOLDER=/opt/cypress-cache
RUN npm install --prefix /opt/body-validator --ignore-scripts --save-exact acorn@8.15.0
RUN mv /root/.cache/Cypress /opt/cypress-cache && chmod -R a+rX /opt/cypress-cache
RUN git clone https://github.com/tastejs/todomvc.git /opt/todomvc \
    && cd /opt/todomvc \
    && git checkout 1f2bd7f0a1fa8c602284451d282c3821d0d96aec
COPY todomvc-escape-oracle.patch /tmp/oracle.patch
COPY todomvc-visual-support.js /opt/todomvc/cypress/support/qualification-visual.js
RUN cd /opt/todomvc && git apply /tmp/oracle.patch \
    && CYPRESS_INSTALL_BINARY=0 npm ci --ignore-scripts \
    && npm --prefix examples/vue ci --ignore-scripts \
    && rm -rf .git /root/.npm \
    && chown -R node:node /opt/todomvc
COPY todomvc-pilot-run.sh /opt/pilot-run.sh
USER node
ENTRYPOINT ["bash", "/opt/pilot-run.sh"]
