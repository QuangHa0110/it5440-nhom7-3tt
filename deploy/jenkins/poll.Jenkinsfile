// Job "pr-triage-poll": thay webhook khi GitHub không gọi tới được Jenkins (chạy trên máy cá nhân).
// Mỗi 2 phút hỏi PR đang mở của từng repo trong PR_TRIAGE_ALLOWED_REPOS,
// rồi kích job pr-triage cho PR mới hoặc vừa có commit mới. Ở công ty dùng webhook và tắt job này (PR_TRIAGE_POLL=0).
pipeline {
    agent any
    options {
        disableConcurrentBuilds()
        timeout(time: 5, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }
    environment {
        POLL_STATE = '/data/poll-state.json'
    }
    stages {
        stage('poll') {
            steps {
                script {
                    def out = ''
                    withCredentials([usernamePassword(credentialsId: 'github-token',
                                                      usernameVariable: 'GH_USER', passwordVariable: 'GITHUB_TOKEN')]) {
                        out = sh(returnStdout: true,
                                 script: 'pr-triage ci poll --state "$POLL_STATE"').trim()
                    }
                    def rows = out ? out.split('\n') : []
                    for (row in rows) {
                        def f = row.split('\t')
                        build job: 'pr-triage', wait: false, parameters: [
                            string(name: 'REPO', value: f[0]),
                            string(name: 'PR', value: f[1]),
                            string(name: 'BASE_REF', value: f[2]),
                            string(name: 'HEAD_SHA', value: f[3]),
                        ]
                    }
                    // Chỉ ghi nhận "đã thấy" sau khi đã kích xong mọi build.
                    sh 'mv "$POLL_STATE.next" "$POLL_STATE"'
                    currentBuild.description = "kích ${rows.size()} PR"
                }
            }
        }
    }
}
