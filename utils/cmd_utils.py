import subprocess

def cmd(commonds):
    '''
    定义命令执行方法

    @:param commonds [] 执行的命令
    '''
    process = subprocess.run(commonds,text=True,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if process.returncode == 0:
        return True,process.stdout
    else:
        return False,process.stdout

def maven_deploy_define_cmd(url,repositoryId,file_path,groupId,artifactId,version,packaging="jar"):
    "执行mvn上传命令，定义的groupId,artifactId,vesion,packaging"
    commands=["mvn","deploy:deploy-file",
              f"-Dfile={file_path}",
              f"-DgroupId={groupId}",
              f"-DartifactId={artifactId}",
              f"-Dversion={version}",
              f"-Durl={url}",
              f"-DrepositoryId={repositoryId}",
              f"-Dpackaging={packaging}"]
    f,t = cmd(commands)
    return mvn_cmd_format(f,t)

def maven_deploy_jar_by_pom_cmd(url,repositoryId,file_path,pom_file):
    "执行maven上传命令，通过jar的pom文件上传jar的格式"
    commands = ["mvn", "deploy:deploy-file",
                f"-Dfile={file_path}",
                f"-DpomFile={pom_file}",
                f"-Durl={url}",
                f"-DrepositoryId={repositoryId}",
                f"-Dpackaging=jar"
                ]
    f, t = cmd(commands)
    return mvn_cmd_format(f, t)

def maven_deploy_pom_by_pom_cmd(url,repositoryId,pom_file):
    "执行maven上传命令，上传pom文件"
    commands = ["mvn", "deploy:deploy-file",
                f"-Dfile={pom_file}",
                f"-DpomFile={pom_file}",
                f"-Durl={url}",
                f"-DrepositoryId={repositoryId}",
                f"-Dpackaging=pom"
                ]
    f, t = cmd(commands)
    return mvn_cmd_format(f,t)

def mvn_cmd_format(flag,text):
    text = str(text)
    if flag == True:
        if "[INFO] BUILD SUCCESS" in text:
            return True, "ok"
        else:
            return False, text
    else:
        return flag, text