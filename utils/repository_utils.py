import os


def scan_repository(path,type='mvn'):
    if type!='mvn':
        data = {}
        for root, dirs, files in os.walk(path):
            for name in files:
                filenames = str(name)
                apath = os.path.join(root, name)
                data[filenames]=apath
        return data
    else:
        data = {}
        for root, dirs, files in os.walk(path):
            for name in files:
                filenames = str(name)
                if filenames.endswith("jar") or filenames.endswith("pom"):
                    apath = os.path.join(root,name)
                    rpath = str(root).replace(path,'')
                    repoArr = rpath.split('\\')
                    typeStr = name[-3:]
                    length = len(repoArr)
                    groupIdArr = []
                    for i in range(length-2):
                        if repoArr[i]!='':
                            groupIdArr.append(repoArr[i])
                    groupId = ".".join(groupIdArr)
                    artifactId = repoArr[length-2]
                    version = repoArr[length-1]
                    if rpath not in data:
                        data[rpath] ={}
                        data[rpath]['groupId'] = groupId
                        data[rpath]['artifactId'] = artifactId
                        data[rpath]['version'] = version
                    data[rpath][typeStr] = name
                    typePath = typeStr+'path'
                    data[rpath][typePath] = apath
        return data