// https://blog.csdn.net/diantun00/article/details/81075007
pipeline {
    agent any
    // agent { label 'my-label' }
    // agent {
    //     node {
    //         label 'my-label'
    //         customWorkspace '/some/other/path'
    //     }
    // }
    // agent {
    //     docker {
    //         image 'nginx:1.12.2'
    //         label 'my-label'
    //         args '-v /tmp:/tmp'
    //     }
    // }
    options{
        timeout(time:1,unit: 'HOURS')
    }
    stages {
        node {
            stage('Example') {
                try {
                    sh 'exit 1'
                }
                catch (exc) {
                    echo 'Something failed, I should sound the klaxons!'
                    throw
                }
            }
        }
        stage('Example'){
            steps {
                def singlyQuoted = 'Hello'
                echo 'Hello world'
                echo "I said, Hello Mr. ${username}"   // $变量只支持双引号中
                checkout 'scm'
                sh 'make'
                sh([script: 'echo hello'])
                git url: 'git://example.com/amazing-project.git', branch: 'master'
                git([url: 'git://example.com/amazing-project.git', branch: 'master'])
                bat 'make check'
                junit 'reports/**/*.xml'
                script {
                    def browsers = ['chrome', 'firefox']
                    for (int i = 0; i < browsers.size(); ++i) {
                        echo "Testing the ${browsers[i]} browser"
                    }
                }
            }
        }
        stage('Test') {
            parallel linux: {
                node('linux') {
                    checkout scm
                    try {
                        unstash 'app'
                        sh 'make check'
                    }
                    finally {
                        junit '**/target/*.xml'
                    }
                }
            },
            windows: {
                node('windows') {
                    /* .. snip .. */
                }
            }
        }
    }
    post {  // 构建后操作，允许声明许多不同的“post conditions”，例如：always，unstable，success，failure，和 changed。
        always {
            echo 'say goodbay'
        }
        failure {
            mail to: team@example.com, subject: 'The Pipeline failed :('
        }
    }
    paramenters {   // 接受用户指定的参数
        choice(name:'PerformMavenRelease',choices:'False\nTrue',description:'desc')
        password(name:'CredsToUse',description:'Apassword to build with',defaultValue:'')

    }
    environment {
        BUILD_USR_CHOICE="${params.PerformMavenRelease}"
        BUILD_USR_CREDS="${params.CredsToUse}"
    }
    triggers {cron('H 4/* 0 0 1-5')}
    // triggers {pollSCM('H 4/* 0 0 1-5')}
    // triggers {upstream(upstreamProjects:'job1,job2',threshold:hudson.model.Result.SUCCESS)}
}