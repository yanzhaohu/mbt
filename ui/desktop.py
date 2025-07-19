import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils import java_env_check,maven_env_check,load_settings_xml,cache_put
from threading import Thread
from .maven_batch_frame import MavenBatchFrame

class AppStartFrame(ttk.Frame):

    def __init__(self, master):
        super().__init__(master, padding=15)
        self.pack(fill=BOTH, expand=YES)
        self.create_meter()

    def create_meter(self):
        self.meter = ttk.Meter(
            metersize=360,
            padding=5,
            amountused=0,
            amounttotal=100,
            arcoffset=100,
            metertype="info.TMeter",
            showtext=False,
            subtext="loading...",
            interactive=False,
        )
        self.meter.pack()
        Thread(
            target=self.checkInit,
            args=(),
            daemon=False
        ).start()


    def checkInit(self):
        javaFlag = java_env_check()
        self.meter.configure(amountused=30)
        mavneFlag = maven_env_check()
        self.meter.configure(amountused=60)
        settingFlag, data = load_settings_xml()
        self.meter.configure(amountused=90)
        cache_put("javaFlag",javaFlag)
        cache_put("mavenFlag",mavneFlag)
        cache_put("settingFlag",settingFlag)
        if data is None:
            data = {'settingXml':'','localRepository':'','mirror':[]}
        cache_put("settingData",data)
        self.meter.configure(amountused=100)
        self.meter.destroy()
        MavenBatchFrame(self.master)
        self.master.place_window_center()




def app_run():
    app = ttk.Window("maven批量上传工具", "superhero",iconphoto="mbt.png")
    AppStartFrame(app)
    app.place_window_center()
    app.mainloop()