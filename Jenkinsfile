pipeline {

    agent {
        label 'payerlink-slave'
    }

    parameters {

        choice(
            name: 'ACTION',
            choices: ['DELETE', 'RESTORE'],
            description: 'Select operation mode'
        )

        booleanParam(
            name: 'DRY_RUN',
            defaultValue: true,
            description: 'If true → no actual IAM changes'
        )

        choice(
            name: 'RESTORE_SCOPE',
            choices: ['FULL', 'ACCOUNT', 'ROLE'],
            description: 'Used only for RESTORE'
        )

        string(
            name: 'ACCOUNT_ID',
            defaultValue: '',
            description: 'Used for ACCOUNT/ROLE restore'
        )

        string(
            name: 'ROLE_NAMES',
            defaultValue: '',
            description: 'Comma-separated roles (ROLE restore only)'
        )

        string(
            name: 'BACKUP_FILE',
            defaultValue: '',
            description: 'Selected backup JSON from GitLab branch (RESTORE only)'
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

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    pip install --upgrade pip
                    pip install boto3 slack_sdk
                '''
            }
        }

        stage('Execute IAM Role Cleaner') {
            steps {
                script {

                    if (params.ACTION == 'DELETE') {

                        sh """
                        python3 main.py \
                          --csv-file inputs/roles.csv \
                          --dry-run ${params.DRY_RUN} \
                          --build-number ${BUILD_NUMBER} \
                          --build-url ${BUILD_URL} \
                          --git-commit \$(git rev-parse HEAD)
                        """

                    } else {

                        sh """
                        python3 restore_roles.py \
                          --backup-file ${params.BACKUP_FILE} \
                          --restore-scope ${params.RESTORE_SCOPE} \
                          --account-id ${params.ACCOUNT_ID} \
                          --role-names "${params.ROLE_NAMES}" \
                          --dry-run ${params.DRY_RUN} \
                          --restore-profiles true
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

        stage('GitLab Backup Push') {
            when {
                expression { params.ACTION == 'DELETE' }
            }
            steps {
                script {
                    echo "Future enhancement: push backups to git branch iam-role-cleaner-backups"
                }
            }
        }
    }

    post {

        always {
            echo "Pipeline execution completed"
        }

        success {
            echo "IAM Role Cleaner SUCCESS"
        }

        failure {
            echo "IAM Role Cleaner FAILED - check logs"
        }
    }
}