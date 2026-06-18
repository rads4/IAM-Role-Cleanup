pipeline {

    agent {
        label 'payerlink-slave'
    }

    parameters {

        choice(
            name: 'ACTION',
            choices: ['DELETE', 'RESTORE'],
            description: 'IAM operation mode'
        )

        booleanParam(
            name: 'DRY_RUN',
            defaultValue: true,
            description: 'TRUE = simulate only, FALSE = real execution'
        )

        choice(
            name: 'RESTORE_SCOPE',
            choices: ['FULL', 'ACCOUNT', 'ROLE'],
            description: 'RESTORE granularity (used only for RESTORE)'
        )

        string(
            name: 'ACCOUNT_ID',
            defaultValue: '',
            description: 'Required for ACCOUNT or ROLE restore'
        )

        string(
            name: 'ROLE_NAMES',
            defaultValue: '',
            description: 'Comma-separated roles (ROLE restore only)'
        )

        string(
            name: 'BACKUP_FILE',
            defaultValue: '',
            description: 'Selected backup file from iam-role-cleaner-backups branch'
        )
    }

    stages {

        stage('Build Info') {
            steps {
                script {
                    def buildNumber = env.BUILD_NUMBER
                    def buildDate = new Date().format('yyyy-MM-dd')
                    def mode = "${params.ACTION}-${params.DRY_RUN ? 'DRY' : 'LIVE'}"

                    buildName "${buildDate}_B${buildNumber}_${mode}"
                }
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    pip install boto3 slack_sdk
                '''
            }
        }

        stage('Execute IAM Cleaner') {
            steps {
                script {

                    if (params.ACTION == 'DELETE') {

                        echo "Starting DELETE flow"

                        sh """
                        python3 main.py \
                          --csv-file inputs/roles.csv \
                          --dry-run ${params.DRY_RUN} \
                          --build-number ${BUILD_NUMBER} \
                          --build-url ${BUILD_URL} \
                          --git-commit \$(git rev-parse HEAD)
                        """

                    } else {

                        echo "Starting RESTORE flow"

                        sh """
                        python3 restore_roles.py \
                          --backup-file ${params.BACKUP_FILE} \
                          --restore-scope ${params.RESTORE_SCOPE} \
                          --account-id ${params.ACCOUNT_ID} \
                          --role-names "${params.ROLE_NAMES}" \
                          --dry-run ${params.DRY_RUN}
                        """
                    }
                }
            }
        }

        stage('Archive Artifacts') {
            steps {
                archiveArtifacts artifacts: '''
                    backups/**/*,
                    output/**/*,
                    *.json
                ''', allowEmptyArchive: true
            }
        }

        stage('Push Backup Branch') {

            when {
                expression {
                    params.ACTION == 'DELETE' &&
                    !params.DRY_RUN
                }
            }

            steps {

                script {

                    sh '''
                    echo "======================================"
                    echo "PUSHING BACKUPS TO BACKUP BRANCH"
                    echo "======================================"

                    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

                    git fetch origin

                    if git show-ref --verify --quiet refs/heads/iam-role-cleaner-backups
                    then
                        git checkout iam-role-cleaner-backups
                    else
                        git checkout -b iam-role-cleaner-backups origin/iam-role-cleaner-backups
                    fi

                    mkdir -p backup-history

                    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

                    TARGET_DIR="backup-history/${TIMESTAMP}"

                    mkdir -p "${TARGET_DIR}"

                    cp -r backups/* "${TARGET_DIR}/" 2>/dev/null || true

                    cp -r output/* "${TARGET_DIR}/" 2>/dev/null || true

                    git add .

                    git commit \
                    -m "IAM Cleaner Backup - Build ${BUILD_NUMBER}" \
                    || true

                    git push origin iam-role-cleaner-backups

                    git checkout ${CURRENT_BRANCH}

                    echo "Backup push completed"
                    '''
                }
            }
        }

        stage('Summary') {
            steps {
                echo "======================================"
                echo "IAM ROLE CLEANER EXECUTION COMPLETE"
                echo "ACTION      : ${params.ACTION}"
                echo "DRY RUN     : ${params.DRY_RUN}"
                echo "BUILD       : ${env.BUILD_NUMBER}"
                echo "======================================"
            }
        }
    }

    post {

        success {
            echo "Pipeline SUCCESS"
        }

        failure {
            echo "Pipeline FAILED - check logs"
        }

        always {
            cleanWs()
        }
    }
}