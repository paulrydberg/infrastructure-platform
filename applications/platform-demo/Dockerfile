# platform-demo — first versioned container application for
# infrastructure-platform (Phase 1: local container foundation).
#
# Purpose: a minimal, dependency-light HTTP service that exists to prove the
# platform's container lifecycle: build → run → health → logs → restart →
# recover. It demonstrates deterministic, reproducible deployment practice:
# pinned base image, non-root user, health check, explicit resource limits,
# no secrets, no volumes required.
FROM python:3.12-alpine3.20

LABEL org.opencontainers.image.title="infrastructure-platform-demo"
LABEL org.opencontainers.image.description="Phase 1 lifecycle validation service"
LABEL org.opencontainers.image.source="https://github.com/paulrydberg/infrastructure-platform"

# non-root user; no package installs needed (stdlib only) — deterministic build
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY app.py /app/app.py
USER app

EXPOSE 8080
# container-native healthcheck: fails until the app answers, self-heals via restart policy
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2).status==200 else 1)"

CMD ["python", "-u", "/app/app.py"]
