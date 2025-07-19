import os
import pathlib
from queue import Queue
from threading import Thread
from tkinter.filedialog import askdirectory,asksaveasfilename,askopenfilename

import ttkbootstrap as ttk
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox, MessageDialog
from utils import cache_put,cache_get, setting_xml_parse,scan_repository
from utils.excel_utils import read_excel,write_excel
from utils.cmd_utils import maven_deploy_define_cmd,maven_deploy_jar_by_pom_cmd,maven_deploy_pom_by_pom_cmd
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

class MavenBatchFrame(ttk.Frame):

    queue = Queue()

    def __init__(self, master):
        super().__init__(master, padding=15)
        self.pack(fill=BOTH, expand=YES)
        self.error_count = 0
        self.envFlag = True
        try:
            self.term_var = ttk.StringVar(value='md')
            self.type_var = ttk.StringVar(value='jar')
            self.templ_var = ttk.StringVar(value='')
            self.thread_num = ttk.IntVar(value=8)
            self.thread_open = ttk.BooleanVar(value=True)

            try:
                settingData = cache_get("settingData")
                self.mirrors_vars = settingData['mirror']
                self.repo_var = ttk.StringVar(value=settingData['localRepository'])
                mirrorValues = []
                for mirr in self.mirrors_vars:
                    mirrorValues.append(mirr)
                self.mirror = ttk.StringVar(value=mirrorValues[0])
                self.mirror_url = ttk.StringVar(value=self.mirrors_vars[mirrorValues[0]]['url'])
            except Exception as e:
                self.mirrors_vars = []
                self.repo_var = ttk.StringVar()
                self.mirror = ttk.StringVar()
                self.mirror_url = ttk.StringVar()
            self.mirror_values = mirrorValues

            self.settings_xml = settingData['settingXml']
            self.def_row = None
            self.path_imp_ent = None

            option_text = '配置'
            self.option_lf = ttk.Labelframe(self, text=option_text, padding=15)
            self.option_lf.pack(fill=X, expand=YES, anchor=N)

            self.create_thread_row()
            self.create_mirror_row()
            self.create_type_row()
            self.create_localRepository_row()
            self.create_handler_btn()
            self.create_progress_bar()
            self.create_results_view()
        except Exception as e:
            print(e)
        self.after(500, self.checkalert)
        self.after(200, self.check_update_ui)

    def checkalert(self):
        javaFlag = cache_get("javaFlag")
        mavenFlag = cache_get("mavenFlag")
        settingFlag = cache_get("settingFlag")
        checkMsg = ''
        if not javaFlag:
            checkMsg = checkMsg+'java环境异常\n'
        if not mavenFlag:
            checkMsg = checkMsg + 'maven环境异常\n'
        if not settingFlag:
            checkMsg = checkMsg + 'maven配置异常\n'
        if checkMsg !='':
            self.envFlag = False
            Messagebox.show_warning(message=checkMsg+"无法正常运行", title="警告",parent=self.opt_btn)

    def create_thread_row(self):
        t_row = ttk.Frame(self.option_lf)
        t_row.pack(fill=X, expand=YES)
        t_open_lbl = ttk.Label(t_row, text="并发开关：", width=12)
        t_open_lbl.pack(side=LEFT, padx=(15, 0))
        t_open_btn = ttk.Checkbutton(t_row,variable=self.thread_open,bootstyle="success-round-toggle")
        t_open_btn.pack(side=LEFT, padx=(15, 0))
        t_num_lbl = ttk.Label(t_row, text="并发数：", width=6)
        t_num_lbl.pack(side=LEFT, padx=(15, 0))
        t_max_num= 2*os.cpu_count()+1
        t_sb_btn = ttk.Spinbox(t_row,from_=2,to=t_max_num,
                               textvariable=self.thread_num,
                               bootstyle=PRIMARY,
                               state=READONLY,
                               width=12,)
        t_sb_btn.pack(side=LEFT,padx=(15, 0))

    def create_mirror_row(self):
        mirror_row = ttk.Frame(self.option_lf)
        mirror_row.pack(fill=X, expand=YES,pady=15)
        mirror_lbl = ttk.Label(mirror_row, text="仓库选择：", width=12)
        mirror_lbl.pack(side=LEFT, padx=(15, 0))
        self.mirror_select = ttk.Combobox(mirror_row,
                                     textvariable=self.mirror,
                                     values=self.mirror_values,
                                     state=READONLY,
                                     width=5)
        self.mirror.trace('w',self.on_mirror_url_change)
        self.mirror_select.pack(side=LEFT, fill=X, expand=YES, padx=5)
        mirror_url_lbl = ttk.Label(mirror_row, text="仓库地址：", width=8)
        mirror_url_lbl.pack(side=LEFT, padx=(5, 0))
        mirror_url_ent = ttk.Entry(mirror_row, textvariable=self.mirror_url, state=READONLY)
        mirror_url_ent.pack(side=LEFT, fill=X, expand=YES, padx=5)
        self.mirror_url_toolTip = ToolTip(mirror_url_ent, text=self.mirror_url.get())
        self.setting_browse_btn = ttk.Button(
            master=mirror_row,
            text="选择配置",
            command=self.on_select_setting,
            width=8
        )
        self.setting_browse_btn.pack(side=LEFT, padx=5)

    def create_type_row(self):
        type_row = ttk.Frame(self.option_lf)
        type_row.pack(fill=X, expand=YES, pady=15)
        type_lbl = ttk.Label(type_row, text="上传类型：", width=12)
        type_lbl.pack(side=LEFT, padx=(15, 0))

        jar_opt = ttk.Radiobutton(
            master=type_row,
            text="jar",
            variable=self.type_var,
            value="jar",
            command=self.destroy_define_row
        )
        jar_opt.pack(side=LEFT,padx=12)

        pom_opt = ttk.Radiobutton(
            master=type_row,
            text="pom",
            variable=self.type_var,
            value="pom",
            command=self.destroy_define_row
        )
        pom_opt.pack(side=LEFT, padx=15)

        jar_pom_opt = ttk.Radiobutton(
            master=type_row,
            text="jar&pom",
            variable=self.type_var,
            value="jar&pom",
            command=self.destroy_define_row
        )
        jar_pom_opt.pack(side=LEFT,padx=15)

        def_opt = ttk.Radiobutton(
            master=type_row,
            text="自定义",
            variable=self.type_var,
            value="def",
            command=self.define_row
        )
        def_opt.pack(side=LEFT)
        jar_opt.invoke()

    def create_localRepository_row(self):
        path_row = ttk.Frame(self.option_lf)
        path_row.pack(fill=X, expand=YES)
        path_lbl = ttk.Label(path_row, text="仓库本地路径：", width=12)
        path_lbl.pack(side=LEFT, padx=(15, 0))
        path_ent = ttk.Entry(path_row, textvariable=self.repo_var,state=READONLY)
        path_ent.pack(side=LEFT, fill=X, expand=YES, padx=5)
        browse_btn = ttk.Button(
            master=path_row,
            text="选择",
            command=self.on_local_browse,
            width=8
        )
        browse_btn.pack(side=LEFT, padx=5)

    def destroy_define_row(self):
        try:
            if self.def_row and self.def_row.destroy:
                self.def_row.destroy()
        except Exception as e:
            print(e)

    def define_row(self):
        self.destroy_define_row()
        self.def_row = ttk.Frame(self.option_lf)
        self.def_row.pack(fill=X, expand=YES,pady=15)
        path_lbl = ttk.Label(self.def_row, text="数据导入：", width=12)
        path_lbl.pack(side=LEFT, padx=(15, 0))
        self.path_imp_ent = ttk.Entry(self.def_row, textvariable=self.templ_var, state=READONLY)
        self.path_imp_ent.pack(side=LEFT, fill=X, expand=YES, padx=5)
        browse_btn = ttk.Button(
            master=self.def_row,
            text="选择",
            command=self.on_select_impl,
            width=8
        )
        browse_btn.pack(side=LEFT, padx=5)
        downLoad_btn = ttk.Button(
            master=self.def_row,
            text="下载",
            command=self.on_template_download,
            width=8,
            bootstyle="info-outline"
        )
        downLoad_btn.pack(side=LEFT, padx=5)

    def create_handler_btn(self):
        btn_row = ttk.Frame(self)
        btn_row.pack(expand=YES, pady=15)
        self.opt_btn = ttk.Button(
            master=btn_row,
            text="开始上传",
            command=self.on_mvn_upload,
            width=8
        )
        self.opt_btn.grid(row=0,column=0,padx=10)
        self.download_btn = ttk.Button(
            master=btn_row,
            text="结果下载",
            command=self.on_download_result,
            width=8,
            bootstyle="info-outline"
        )
        self.download_btn.grid(row=0,column=1)

    def create_progress_bar(self):
        self.progress_bar = ttk.Floodgauge(self,mask="0%",value=0,bootstyle="success")
        self.progress_bar.pack(fill=X, expand=YES)

    def create_results_view(self):
        frame = ttk.Frame(self)
        frame.pack()
        scroll = ttk.Scrollbar(frame, orient=VERTICAL)
        scroll.pack(side=RIGHT, fill=Y)
        self.resultview = ttk.Treeview(
            master=frame,
            bootstyle=INFO,
            columns=[0, 1, 2, 3, 4, 5, 6],
            show=HEADINGS,
            yscrollcommand=scroll.set
        )
        self.resultview.pack(fill=BOTH)
        self.resultview.heading(0, text='groupId', anchor=W)
        self.resultview.heading(1, text='artifactId', anchor=W)
        self.resultview.heading(2, text='version', anchor=W)
        self.resultview.heading(3, text='type', anchor=W)
        self.resultview.heading(4, text='fileName', anchor=W)
        self.resultview.heading(5, text='上传状态', anchor=W)
        self.resultview.heading(6, text='结果', anchor=W)
        self.resultview.column(
            column=0,
            anchor=W,
            stretch=False
        )
        self.resultview.column(
            column=1,
            anchor=W,
            stretch=False
        )
        self.resultview.column(
            column=2,
            anchor=W,
            width=150
        )
        self.resultview.column(
            column=3,
            anchor=W,
            width=100
        )
        self.resultview.column(
            column=4,
            anchor=W,
        )
        self.resultview.column(
            column=5,
            anchor=W,
        )
        self.resultview.column(
            column=6,
            anchor=W,
        )
        self.tmenu = ttk.Menu(self,tearoff=0)
        self.tmenu.add_command(label="详情",command=self.show_tree_detail)
        self.tmenu.add_command(label="重传",command=self.re_upload_detail)

        self.resultview.bind('<Button-3>',self.show_menu)
        scroll.configure(command=self.resultview.yview)

    def show_menu(self,event):
        self.resultview.selection_set(self.resultview.identify_row(event.y))  # 设置选中行
        self.tmenu.post(event.x_root, event.y_root)  # 在鼠标位

    def create_dialog_with_scrolledtext(self,msg):
        # 创建弹窗
        dialog = ttk.Window(themename="superhero")
        dialog.title("详情")
        dialog.geometry("400x300")

        # 创建带滚动条的文本框
        text_area = ttk.ScrolledText(dialog, wrap=WORD)
        text_area.pack(fill=BOTH, expand=True)

        # 填充一些文本内容以显示滚动条的效果
        text_area.insert(END, msg)
        dialog.place_window_center()
        dialog.mainloop()

    def show_tree_detail(self):
        iid = self.resultview.selection()
        values = self.resultview.item(iid, 'values')
        msg = (f"groupId:{values[0]}\r\nartifactId"+
               f":{values[1]}\r\nversion:{values[2]}\r\ntype"+
               f":{values[3]}\r\nfileName:{values[4]}\r\n"+
               f"上传状态:{values[5]}\r\n结果:\r\n{values[6]}")
        self.create_dialog_with_scrolledtext(msg)

    def re_upload_detail(self):
        self.error_count = 0
        self.progress_bar.configure(maximum=1, value=0, mask="0%")
        iid = self.resultview.selection()
        typeStr = self.type_var.get()
        Thread(
            target=self.__re_mvn_upload_execute__,
            args=(iid,typeStr),
            daemon=False
        ).start()

    def __re_mvn_upload_execute__(self,iid,typeStr):
        if 'def' == typeStr:
            self.__def_mvn_execute__(iid)
        else:
            self.__mvn_execute__(iid)

    def path_to_str(self,path):
        return str(pathlib.Path(path).absolute())

    def on_select_setting(self):
        path = askopenfilename(defaultextension=[('Xml File','*.xml')],filetypes=[('Xml File','*.xml')],title="选择配置")
        if path:
            self.settings_xml = self.path_to_str(path)
            self.handler_select_xml()

    def handler_select_xml(self):
        settingData = setting_xml_parse(self.settings_xml)
        try:
            self.repo_var.set(settingData['localRepository'])
            self.mirrors_vars = settingData['mirror']
            mirrorValues = []
            for mirr in self.mirrors_vars:
                mirrorValues.append(mirr)
            self.mirror.set(mirrorValues[0])
            self.mirror_values = mirrorValues
            self.mirror_url.set(self.mirrors_vars[mirrorValues[0]]['url'])
            self.settings_xml = settingData['settingXml']
            self.mirror_select.configure(values=self.mirror_values)
        except Exception as e:
            Messagebox.show_warning(message="解析异常，请检查配置是否正确",title="警告",parent=self.opt_btn)

    def on_local_browse(self):
        path = askdirectory(title="选择文件夹")
        if path:
            self.repo_var.set(self.path_to_str(path))

    def on_select_impl(self):
        path = askopenfilename(defaultextension=[('Excel File', '*.xls;*.xlsx')], filetypes=[('Excel File', '*.xls;*.xlsx')],
                               title="选择数据")
        if path:
            xls_excel = self.path_to_str(path)
            self.templ_var.set(xls_excel)

    def on_template_download(self):
        filetypes = [('Excel Files', '*.xlsx,*.xls')]
        file = asksaveasfilename(filetypes = filetypes, defaultextension = filetypes,initialfile="maven_template.xlsx")
        data = pd.DataFrame({'groupId':['io.netty'],'artifactId':['netty'],'version':['3.9.0.Final'],'type':['jar'],'fileName':['netty-3.9.0.Final.jar']})
        write_excel(file,data)
        self.templ_var.set(file)
        Messagebox.show_info("保存完成！",title="提示",parent=self.opt_btn)

    def on_mirror_url_change(self,*args):
        key = self.mirror.get()
        self.mirror_url.set(self.mirrors_vars[key]['url'])
        self.mirror_url_toolTip.text = self.mirror_url.get()

    def on_mvn_upload(self):
        if self.envFlag == False:
            self.checkalert()
            return
        self.result_view_clearn()
        self.error_count = 0
        typeStr = self.type_var.get()
        if 'def' == typeStr:
            self.def_handler()
        else:
            self.file_handler(typeStr)


    def on_download_result(self):
        filetypes = [('Excel Files', '*.xlsx,*.xls')]
        file = asksaveasfilename(filetypes=filetypes, defaultextension=filetypes, initialfile="maven_result_dowload.xlsx")
        root_nodes = self.resultview.get_children()
        if len(root_nodes) >0:
            data_result = {'groupId': [], 'artifactId': [], 'version': [], 'type': [],
                 'fileName': [],'上传状态':[],'结果':[]}
            for iid in root_nodes:
                values = self.resultview.item(iid, 'values')
                data_result['groupId'].append(values[0])
                data_result['artifactId'].append(values[1])
                data_result['version'].append(values[2])
                data_result['type'].append(values[3])
                data_result['fileName'].append(values[4])
                data_result['上传状态'].append(values[5])
                data_result['结果'].append(values[6])
            data = pd.DataFrame(data_result)
            write_excel(file, data)
            Messagebox.show_info("下载成功！", title="提示", parent=self.opt_btn)
        else:
            Messagebox.show_info("没有数据无法下载！", title="提示", parent=self.opt_btn)

    def file_handler(self,typeStr):
        data = scan_repository(self.repo_var.get())
        # 缓存数据
        cache_put('scan_repository',data)
        if 'jar&pom' == typeStr:
            self.__data_hadnler__(data,'jar')
            self.__data_hadnler__(data,'pom')
        else:
            self.__data_hadnler__(data,typeStr)

    def __data_hadnler__(self,data,typeStr):
        select_typeStr = self.type_var.get()
        for k in data:
            if typeStr in data[k]:
                if 'pom' == typeStr and 'jar' in data[k] and data[k]['jar'] is not None and data[k]['jar']!='':
                    continue
                item = []
                item.append(data[k]['groupId'])
                item.append(data[k]['artifactId'])
                item.append(data[k]['version'])
                item.append(typeStr)
                item.append(data[k][typeStr])
                item.append('待上传')
                item.append('')
                self.result_view_inser(item)
        if 'jar&pom' == select_typeStr and 'jar' == typeStr:
            return
        root_nodes = self.resultview.get_children()
        if len(root_nodes) >0:
            self.progress_bar.configure(maximum=len(root_nodes),value=0,mask="0%")
            iid = root_nodes[0]
            self.resultview.selection_set(iid)
            self.resultview.see(iid)
            Thread(
                target=self.mvn_upload_execute,
                args=(),
                daemon=False
            ).start()
    # excel解析上传
    def def_handler(self):
        tmpl_path = self.templ_var.get()
        pd = read_excel(tmpl_path)
        pd_val = pd.values
        if len(pd_val) > 0:
            for item in pd_val:
                view_item = []
                [view_item.append(item[i]) for i in range(5)]
                view_item.append('待上传')
                view_item.append('')
                self.result_view_inser(view_item)
            data = scan_repository(self.repo_var.get(),'def')
            cache_put('scan_repository', data)
            self.progress_bar.configure(maximum=len(pd_val), value=0, mask="0%")
            Thread(
                target=self.mvn_upload_execute,
                args=(),
                daemon=False
            ).start()

    def result_view_clearn(self):
        items = self.resultview.get_children()
        [self.resultview.delete(item) for item in items]

    def result_view_inser(self,data):
        self.resultview.insert(
            parent='',
            index=END,
            values=data
        )

    def result_view_update(self,iid,item):
        self.resultview.item(iid,values=item)
        self.resultview.selection_set(iid)
        self.resultview.see(iid)

    def mvn_upload_execute(self):
        nodes = self.resultview.get_children()
        thread_open = self.thread_open.get()
        thread_num  = self.thread_num.get()
        typeStr = self.type_var.get()
        if thread_open:
            if 'def' == typeStr:
                with ThreadPoolExecutor(thread_num) as executor:
                    [executor.submit(self.__def_mvn_execute__, iid) for iid in nodes]
            else:
                with ThreadPoolExecutor(thread_num) as executor:
                    [executor.submit(self.__mvn_execute__,iid) for iid in nodes]
        else:
            if 'def' == typeStr:
                for iid in nodes:
                    self.__def_mvn_execute__(iid)
            else:
                for iid in nodes:
                    self.__mvn_execute__(iid)

    def __def_mvn_execute__(self,iid):
        data = cache_get('scan_repository')
        url = self.mirror_url.get()
        repositoryId = self.mirror.get()
        values = self.resultview.item(iid, 'values')
        groupId = values[0]
        artifactId = values[1]
        version = values[2]
        ftype = values[3]
        file_name = values[4]
        if not file_name in data:
            item = (groupId, artifactId, version, ftype, file_name, '上传失败', '文件不匹配')
            MavenBatchFrame.queue.put([iid, item])
            return
        item = (groupId, artifactId, version, ftype, file_name, '上传中', '')
        MavenBatchFrame.queue.put([iid, item])
        try:
            jp = data[file_name]
            if 'jar' == ftype:
                f, m = maven_deploy_define_cmd(url, repositoryId, jp, groupId, artifactId, version)
            else:
                f, m = maven_deploy_pom_by_pom_cmd(url, repositoryId, jp)
            if f==True:
                item = (groupId, artifactId, version, ftype, file_name, '上传成功', m)
            else:
                item = (groupId, artifactId, version, ftype, file_name, '上传失败', m)
        except Exception as error:
            item = (groupId, artifactId, version, ftype, file_name, '上传失败', str(error))
        finally:
            MavenBatchFrame.queue.put([iid, item])

    def __mvn_execute__(self,iid):
        data = cache_get('scan_repository')
        url = self.mirror_url.get()
        repositoryId = self.mirror.get()
        values = self.resultview.item(iid, 'values')
        groupId = values[0]
        artifactId = values[1]
        version = values[2]
        ftype = values[3]
        file_name = values[4]
        item_key = f'\\{groupId.replace(".", "\\")}\\{artifactId}\\{version}'
        if not item_key in data:
            item = (groupId, artifactId, version, ftype, file_name, '上传失败', '文件不匹配')
            MavenBatchFrame.queue.put([iid, item])
            return
        cfile_name = data[item_key][ftype]
        item = (groupId, artifactId, version, ftype, file_name, '上传中', '')
        MavenBatchFrame.queue.put([iid, item])
        try:
            if file_name == cfile_name:
                if 'jar' == ftype:
                    jp = data[item_key]['jarpath']
                    pp = data[item_key]['pompath']
                    if pp is not None:
                        f, m = maven_deploy_jar_by_pom_cmd(url, repositoryId, jp, pp)
                    else:
                        f, m = maven_deploy_define_cmd(url, repositoryId, jp, groupId, artifactId, version)
                else:
                    pp = data[item_key]['pompath']
                    f, m = maven_deploy_pom_by_pom_cmd(url, repositoryId, pp)
                if f==True:
                    item = (groupId, artifactId, version, ftype, file_name, '上传成功', m)
                else:
                    item = (groupId, artifactId, version, ftype, file_name, '上传失败', m)
            else:
                item = (groupId, artifactId, version, ftype, file_name, '上传失败', '文件匹配错误')
        except Exception as error:
            item = (groupId, artifactId, version, ftype, file_name, '上传失败', str(error))
        except:
            item = (groupId, artifactId, version, ftype, file_name, '上传失败', '未知异常')
        finally:
            MavenBatchFrame.queue.put([iid, item])

    def check_update_ui(self):
        while not MavenBatchFrame.queue.empty():
            data = MavenBatchFrame.queue.get()
            self.result_view_update(data[0],data[1])
            if data[1][5]=="上传中":
                continue
            if data[1][5] == '上传失败':
                self.error_count=self.error_count+1
            value = self.progress_bar.cget("value")+1
            count = self.progress_bar.cget("maximum")
            self.progress_bar.configure(value=value,mask=f'上传进度:{value/count:.2%},失败:{self.error_count}')
        self.after(200,self.check_update_ui)
