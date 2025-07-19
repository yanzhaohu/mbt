from pathlib import Path
from xml.dom.minidom import parse
import xml.dom.minidom

def default_settings_xml_path():
    user_path = Path.home()
    path = Path.joinpath(user_path,".m2","settings.xml")
    return Path.exists(path),str(path)

def load_settings_xml():
   flag,path = default_settings_xml_path()
   if flag:
       data = setting_xml_parse(path)
       return True,data
   else:
       return False,None

def setting_xml_parse(fp):
    root = xml.dom.minidom.parse(fp).documentElement
    localRepositorys = root.getElementsByTagName("localRepository")
    data = {}
    localRepositorypath= ""
    if localRepositorys:
        localRepositorypath = localRepositorys[0].childNodes[0].data
    data['settingXml'] = fp
    data['localRepository'] = localRepositorypath
    data['mirror'] ={}
    servers = root.getElementsByTagName("server")
    for server in servers:
        sid = server.getElementsByTagName("id")[0].childNodes[0].data
        data['mirror'][sid]={}
        username = server.getElementsByTagName("username")[0].childNodes[0].data
        password = server.getElementsByTagName("password")[0].childNodes[0].data
        data['mirror'][sid]['username'] = username
        data['mirror'][sid]['password'] = password
    mirrors = root.getElementsByTagName("mirror")
    for mirror in mirrors:
        mid = mirror.getElementsByTagName("id")[0].childNodes[0].data
        name = mirror.getElementsByTagName("name")[0].childNodes[0].data
        url = mirror.getElementsByTagName("url")[0].childNodes[0].data
        if mid in data:
            data['mirror'][mid]["name"] = name
            data['mirror'][mid]["url"] = url
        else:
            data['mirror'][mid] = {}
            data['mirror'][mid]["name"] = name
            data['mirror'][mid]["url"] = url

    return data