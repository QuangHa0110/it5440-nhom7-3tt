# Jenkins thử nghiệm cục bộ, đã cài sẵn pr-triage (Semgrep đi kèm qua uv).
# Build từ gốc repo: docker compose -f deploy/jenkins/docker-compose.yml build
FROM jenkins/jenkins:lts-jdk21

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/opt/pr-triage/.venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /opt/pr-triage
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY configs ./configs
RUN uv python install 3.12 \
    && uv sync --no-dev --frozen --python 3.12 \
    # semgrep chỉ nằm trong nhóm dev của pyproject, nên cài riêng đúng phiên bản trong uv.lock.
    && uv pip install --python /opt/pr-triage/.venv/bin/python "semgrep==1.185.0" \
    && mkdir -p /data && chown jenkins:jenkins /data

ENV PATH="/opt/pr-triage/.venv/bin:${PATH}" \
    PR_TRIAGE_HOME=/opt/pr-triage \
    PR_TRIAGE_JENKINS=/usr/share/jenkins/pr-triage \
    CASC_JENKINS_CONFIG=/usr/share/jenkins/casc.yaml \
    JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

USER jenkins
COPY deploy/jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY deploy/jenkins/triage.Jenkinsfile deploy/jenkins/poll.Jenkinsfile /usr/share/jenkins/pr-triage/
COPY deploy/jenkins/casc.yaml /usr/share/jenkins/casc.yaml
WORKDIR /var/jenkins_home
