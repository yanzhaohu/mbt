from .cmd_utils import cmd

def java_env_check():
    commonds = ["java", "-version"]
    flag,text = cmd(commonds)
    if flag == True and 'java version' in text:
        return True
    else:
        return False

def maven_env_check():
    commonds = ["mvn", "--version"]
    flag, text = cmd(commonds)
    if flag == True and 'Apache Maven' in text:
        return True
    else:
        return False