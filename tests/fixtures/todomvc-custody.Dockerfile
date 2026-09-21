# Transport-only probe, never a scientific execution image.
FROM debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251
COPY todomvc-pilot-run.sh /runner.sh
ENTRYPOINT ["sh", "-c", "cat /input/response.json > /output/copied-response && cat /input/TodoItem.vue > /output/copied-component"]
