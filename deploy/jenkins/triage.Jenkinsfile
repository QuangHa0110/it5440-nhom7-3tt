// Job trung tâm "pr-triage": mọi PR của mọi repo đi qua đây. Repo được quét không cần sửa gì.
// Được kích bởi: webhook cấp tổ chức (Generic Webhook Trigger), job pr-triage-poll, hoặc "Build with Parameters".
// Tham số (REPO, PR, BASE_REF, HEAD_SHA) và trigger khai báo trong casc.yaml.
// Không có commit status nào gửi lên PR, nên build vàng hay đỏ không bao giờ chặn merge (ADR 0007 D5).
pipeline {
    agent any
    options {
        timeout(time: 15, unit: 'MINUTES')
        timestamps()
        // Một build mỗi lúc: mọi repo ghi chung một store.sqlite.
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '300'))
    }
    environment {
        TRIAGE_DB = '/data/store.sqlite'
    }
    stages {
        stage('allow-list') {
            steps {
                script {
                    currentBuild.displayName = "#${env.BUILD_NUMBER} ${params.REPO}#${params.PR}"
                    def rc = sh(returnStatus: true, script: 'pr-triage ci allowed --repo "$REPO" --pr "$PR"')
                    env.ALLOWED = (rc == 0) ? 'true' : 'false'
                    if (rc != 0) {
                        currentBuild.result = 'NOT_BUILT'
                        currentBuild.description = (rc == 1) ? 'repo ngoài danh sách cho phép' : 'tham số không hợp lệ'
                    }
                }
            }
        }
        stage('triage') {
            when { expression { env.ALLOWED == 'true' } }
            steps {
                sh 'rm -rf out'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    // Mỗi repo một bản clone riêng trong workspace, giữ lại giữa các build cho nhanh.
                    dir("repos/${params.REPO.replace('/', '__')}") {
                        withCredentials([gitUsernamePassword(credentialsId: 'github-token')]) {
                            sh '''
                                set -eu
                                [ -d .git ] || git init -q
                                git remote set-url origin "https://github.com/$REPO.git" 2>/dev/null \
                                  || git remote add origin "https://github.com/$REPO.git"
                                BASE="${BASE_REF:-}"
                                if [ -z "$BASE" ]; then
                                    BASE=$(git ls-remote --symref origin HEAD | awk '/^ref:/ { sub("refs/heads/", "", $2); print $2 }')
                                    echo "BASE_REF trống, dùng nhánh mặc định: $BASE"
                                fi
                                git fetch --no-tags --force origin \
                                  "+refs/heads/$BASE:refs/remotes/origin/base" \
                                  "+refs/pull/$PR/head:refs/remotes/origin/pr"
                            '''
                        }
                        withCredentials([string(credentialsId: 'llm-api-key', variable: 'PR_TRIAGE_LLM_API_KEY')]) {
                            sh '''
                                set -eu
                                # Quét đúng commit mà sự kiện báo; nếu đã bị push đè thì lấy đầu nhánh PR hiện tại.
                                HEAD="${HEAD_SHA:-}"
                                if [ -z "$HEAD" ] || ! git cat-file -e "$HEAD^{commit}" 2>/dev/null; then HEAD=origin/pr; fi
                                pr-triage run --repo . \
                                  --base origin/base --head "$HEAD" --pr "$PR" --repo-alias "$REPO" \
                                  --mode "${PR_TRIAGE_MODE:-shadow}" --display "${PR_TRIAGE_DISPLAY:-B}" \
                                  --rules "$PR_TRIAGE_HOME/configs/semgrep/java-injection.yml" \
                                  --catalog "$PR_TRIAGE_HOME/configs/context/java.yml" \
                                  --db "$TRIAGE_DB" --out "$WORKSPACE/out"
                            '''
                        }
                    }
                }
            }
        }
        stage('publish') {
            when { expression { env.ALLOWED == 'true' && fileExists('out/triage-result.json') } }
            steps {
                // Không gọi LLM ở đây, chỉ đọc kết quả đã kiểm tra và đăng comment (nếu mode là comment).
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    withCredentials([usernamePassword(credentialsId: 'github-token',
                                                      usernameVariable: 'GH_USER', passwordVariable: 'GITHUB_TOKEN')]) {
                        // shadow: chỉ in comment ra console. comment: đăng hoặc cập nhật comment trên PR.
                        sh '''
                            POST=""
                            [ "${PR_TRIAGE_MODE:-shadow}" = comment ] && POST="--post"
                            pr-triage publish --result out/triage-result.json --slug "$REPO" \
                              --pr "$PR" --db "$TRIAGE_DB" $POST
                        '''
                    }
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'out/*.json', allowEmptyArchive: true
        }
    }
}
