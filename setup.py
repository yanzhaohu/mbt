from cx_Freeze import setup,Executable

main_script = 'main.py'

exe = Executable(
    script=main_script,
    base='Win32GUI',
    target_name='maven 批量上传工具',
    icon='mbt.ico'
)

options = {
    'build_exe':{
        'packages':['ttkbootstrap','numpy','pandas','openpyxl'],
        'excludes':['cx_Freeze'],
        'include_files':['mbt.ico','mbt.png'],
        'include_msvcr': True,
        'optimize':2
    }
}

setup(name='maven 批量上传工具',
      version='1.0.0',
      description='用来同步本地仓库到私服或者自定义上传私服',
      options=options,
      executables=[exe]
)
