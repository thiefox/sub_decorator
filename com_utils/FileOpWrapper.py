# -*- coding: UTF-8 -*-

#from bigma import handle_dir
import sys
import os
import time

#os.environ["IMAGEIO_FFMPEG_EXE"] = "d:\\bin\\ffmpeg\\bin\\ffmpeg.exe"

from com_utils import global_data
FFMPEG_PATH = global_data.bm_config.get_ffmpeg_path()
if os.path.isfile(FFMPEG_PATH) :
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

from datetime import datetime 

import shutil
import cv2
#from moviepy.editor import VideoFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip

#import winshell
#import pywin
#from win32com.shell import shell, shellcon
import subprocess

#BIGBROTHER二次分类结尾标志
BIGBROTHER_END_FLAG = ('-C', '-CB', '-PCB', '-B', '-PB', )
RENAME_TMP_ADD = '-tmp-'
FILE_REMOVE_DIR = '~bbtp~'      #要删除的文件全部移入车牌下的这个文件夹

VIDEO_FILE_SUFFIXS = (".mp4", ".wmv", ".avi", ".mkv", ".iso", ".mpg", ".ts", ".mov", ".m2ts", )
AUDIO_FILE_SUFFIXS = ('.wav', '.ape', '.mp3', '.flac', '.aac', '.m4a', '.dff', '.dsf', '.dst', '.iso', '.ogg', )

class video_info :
    definition = int(0)      #清晰度（取视频高度为清晰度，480/720/1080/...)
    seconds = 0         #时长
    size_bytes = 0      #文件大小
    frame_count = 0     #帧数
    fps = 0.00          #每秒帧数
    width = int(0)           #视频宽度
    height = int(0)          #视频高度
    encode_info = ''    #编码器信息
    kbps = 0                #比特率

    def __init__(self) :
        self.definition = self.seconds = self.size_bytes = self.frame_count = self.fps = self.width = self.height = self.kbps = 0
        self.encode_info = ''

    def decode_fourcc(self, cc): # fourcc编码
        self.encode_info = "".join([chr((int(cc) >> 8 * i) & 0xFF) for i in range(4)])
        return

    def print(self) :
        print("video info 1, wdith=%d, height=%d, fps=%.2f帧/秒, frame_count=%d, encode_info=%s." %(self.width, self.height, self.fps, self.frame_count, self.encode_info))   
        print("video info 2, time=%d秒, size=%d, 清晰度=%dp." %(self.seconds, self.size_bytes, self.definition))    
        return

    #是否超宽高比视频（字体需要放大。解决方法：如有resx/resy则丢弃。）示例：嫌疑人X的献身（日版）
    def is_ultra_wide_screen(self) :
        b_ultra_wide = False
        if self.width > 0 and self.height > 0 :
            scale = float(self.width / self.height)
            if scale > 2.1 :
                b_ultra_wide = True
        return b_ultra_wide

    #根据视频的分辨率生成合适的字体大小
    def get_video_font_size(self) -> tuple :
        font_size = None
        if self.width == 0 or self.height == 0 :
            return font_size
        scale = float(self.width / self.height)
        if (self.height >= 2000 and self.height <= 2160) and (scale > 1.66 and scale < 1.86) :        #4K默认
            font_size = (18, 15)
        elif (self.height >= 1588 and self.height <= 1648) and (scale > 2.32 and scale < 2.43) :        #宽屏4K
            font_size = (19, 16)
        elif (self.height >= 958 and self.height <=1080) and (scale > 1.62 and scale < 2.01) :        #标准1080P默认
            font_size = (18, 15)
        elif (self.height >= 960 and self.height <=1080) and (scale > 1.30 and scale < 1.45) :        #老的电视制式转1080P
            font_size = (17, 14)
        elif (self.height >= 800 and self.height <= 880) and (scale > 2.17 and scale < 2.56) :        #宽屏1080P1（因人生切割术增加）
            font_size = (21, 17)
        elif (self.height >= 752 and self.height <= 799) and (scale > 2.17 and scale < 2.56) :        #宽屏1080P2
            font_size = (20, 16)
        elif (self.height >= 688 and self.height <= 720) and (scale > 1.32 and scale < 1.87) :   #标准720P默认
            font_size = (17, 14)
        elif (self.height >= 576 and self.height <= 680) and (scale > 1.77 and scale < 1.89) :      #电视剧
            font_size = (17, 14)
        elif (self.height >= 534 and self.height <= 576) and (scale > 2.21 and scale < 2.41) :   #宽屏720
            font_size = (20, 16)
        elif (self.height >= 540 and self.height <= 576) and (scale > 1.19 and scale < 1.34) :   #老的电视制式转720P
            font_size = (17, 14)
        elif (self.height >= 412 and self.height <= 480) and (scale > 1.46 and scale < 1.76) :   #标准480P默认
            font_size = (18, 15)
        elif (self.height >= 304 and self.height <= 360) and (scale > 1.75 and scale < 1.91) :   #宽屏480P
            font_size = (20, 16)
        elif self.height <= 480 :       #480P
            if scale <= 1.51 :
                font_size = (18, 15)
            elif scale <= 1.91 :
                font_size = (20, 16)
            else :
                font_size = (22, 17)
        elif self.height <= 720 :       #720P
            if scale <= 1.51 :
                font_size = (18, 15)
            elif scale <= 1.91 :
                font_size = (19, 16)
            else :
                font_size = (20, 18)
        elif self.height <= 1080 :      #1080P
            if scale <= 1.51 :
                font_size = (17, 14)
            elif scale <= 1.91 :
                font_size = (18, 15)
            else :
                font_size = (19, 16)
        else  :     #4K
            if scale <= 1.51 :
                font_size = (17, 14)
            elif scale <= 1.91 :
                font_size = (17, 14)
            else :
                font_size = (18, 15)
        return font_size

def get_video_file_info(path_file : str) -> video_info :
    info = video_info()
    try :
        capture = cv2.VideoCapture(path_file)
        info.width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        info.height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        info.definition = info.height
        '''
        info.fps = capture.get(cv2.CAP_PROP_FPS)
        info.frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        info.decode_fourcc(capture.get(cv2.CAP_PROP_FOURCC))
        info.size_bytes = os.path.getsize(path_file)
        #print("video info 1, wdith=%d, height=%d, fps=%.2f帧/秒, fn=%d, fourcc=%s." %(info.width, info.height, info.fps, info.frame_count, info.encode_info))   
        '''
    except Exception as e :
        print("cv2.VideoCapture失败，文件=%s, 原因：%s." %(path_file, str(e)))
        info = None

    if info.seconds == 0 :
        try :
            clip = VideoFileClip(path_file)
            info.seconds = int(clip.duration)
            info.kbps = info.size_bytes * 8 / info.seconds / 1024
        except Exception as e :
            print("VideoFileClip失败，文件=%s, 原因：%s." %(path_file, str(e)))
            pass
    #time_obj = datetime.time(0, 0 , seconds)
    #duration_info = ':'.join(str(seconds).split(':')[1:])
    #print("video info 2, time=%d秒. size=%d." %(info.seconds, info.size_bytes))
    return info

#打印所有的低品质视频信息
def print_low_quality_video(root_dir) :
    print('\n开始检测根目录(%s)...' %root_dir)
    #视频文件
    #VIDEO_FILES = (".mp4", ".wmv", ".avi", ".mkv", ".iso", ".ts", )
    #BLURAY_INFOS = ('.bluray.', '-bluray-', ' bluray ', )
    videos = 0
    lows = 0
    middles = 0
    for p, ds, fs in os.walk(root_dir) :
        for f in fs :
            suffix = os.path.splitext(f)[1]
            for V in VIDEO_FILE_SUFFIXS :
                if suffix.lower() == V.lower() :
                    videos += 1
                    path_file = os.path.join(p, f)
                    if V == '.iso' or V == '.ts' :
                        print('视频文件(%s)无法萃取信息。' %path_file)
                    else :
                        video_info = get_video_file_info(path_file)
                        if video_info is not None :
                            if video_info.definition <= 480 :
                                print('警告：视频文件(%s)为低清晰度(%dP), 时长=%d, 比特率=%d。' %(path_file, video_info.definition, video_info.seconds, video_info.kbps))
                                lows += 1
                            elif video_info.definition <= 720 :
                                print('信息：视频文件(%s)为中清晰度(%dP)，时长=%d, 比特率=%d。' %(path_file, video_info.definition, video_info.seconds, video_info.kbps))
                                middles += 1
                    break
    print('根目录(%s)检测完成，共发现视频文件=%d个，其中中清晰度=%d, 低清晰度=%d个。\n' %(root_dir, videos, middles, lows))
    return

def is_video_file(path_file : str) -> bool :
    for suffix in VIDEO_FILE_SUFFIXS :
        if path_file.lower().endswith(suffix.lower()) :
            return True
    return False

def is_audio_file(path_file : str) -> bool :
    for suffix in AUDIO_FILE_SUFFIXS :
        if path_file.lower().endswith(suffix.lower()) :
            return True
    return False

#取得目录下某种类型的(带路径)文件列表
#only_cur==True，只取当前目录下的文件，忽略子目录。
def get_type_files(dir : str, suffixs : list, only_cur : bool = False) -> list :  
    type_files = []
    for parent, __, files in os.walk(dir, topdown=True) :
        for file in files :
            for suffix in suffixs :
                if file.lower().endswith(suffix.lower()) :
                    type_files.append(os.path.join(parent, file))
                    break
        if only_cur :
            break        
    return type_files

#取得目录下的视频文件列表
def get_video_files(dir : str, only_cur : bool = False) -> list :
    return get_type_files(dir, VIDEO_FILE_SUFFIXS, only_cur=only_cur)
#取得目录下的音频文件列表
def get_audio_files(dir : str, only_cur : bool = False) -> list :
    return get_type_files(dir, AUDIO_FILE_SUFFIXS, only_cur=only_cur)

def gen_log_file_name(desc) :
    if desc == '' :
        desc = '通用日志'
    file_name = ''
    cur_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    log_dir = os.path.join(cur_path, 'log')
    if not os.path.isdir(log_dir) :
        try :
            os.mkdir(log_dir)
        except Exception as e :
             err_info = "创建log目录(%s)失败，原因：%s." %(log_dir, str(e))
             print(err_info)
    str_now = datetime.strftime(datetime.now(), '%Y-%m-%d %H-%M-%S')
    file_name = desc + '-' + str_now + '.txt'
    file_name = os.path.join(log_dir, file_name)
    return file_name

#移动文件或目录(src_obj)到target_dir
def move_file_obj(src_obj : str, target_dir : str) -> str :
    err = ''
    if os.path.exists(src_obj) and os.path.exists(target_dir) and os.path.isdir(target_dir) :
        path_new = os.path.join(target_dir, os.path.basename(src_obj))
        if not os.path.exists(path_new) :
            try :
                shutil.move(src_obj, target_dir)
            except Exception as e :
                err = '移动{}到{}失败，原因={}.'.format(src_obj, target_dir, str(e))
        else :
            err = '新的目标对象{}已存在。'.format(path_new)
    else :
        err = '源{}或目标{}参数异常。'.format(src_obj, target_dir)
    return err

#删除某个目录及之下的所有文件和子文件夹
def del_dir_all(root_dir) :
    err = del_file_obj_recycle(root_dir)
    if err != '' :
        try :
            shutil.rmtree(root_dir)
        except Exception as e:
            err = e
    return err

#确保某个目录存在(上级目录必须存在)。成功返回''，异常返回异常信息。
def confirm_dir(path_name : str) -> str :
    err_info = ''
    if os.path.exists(path_name) and os.path.isdir(path_name) :
        return err_info
    parent_dir = os.path.split(path_name)[0]
    if os.path.exists(parent_dir) and os.path.isdir(parent_dir) :
        try :
            os.mkdir(path_name)
        except Exception as e :
            err_info = "创建目录(%s)失败，原因：%s." %(path_name, str(e))
    else :
        err_info = '目录{}的父目录不存在。'.format(path_name)
    return err_info

#删除所有的物理dummy目录
#to do : 测试后加try except
def del_dummy_physical(root_dir) :
    print('del_dummy_physical开始, root_dir=(%s)...' %(root_dir))
    for p, ds, fs in os.walk(root_dir, topdown=False) :
        print("目录处理：path=%s, dirs=%d, files=%d." %(p, len(ds), len(fs)))
        pd_name = os.path.basename(p)
        if pd_name.lower() == FILE_REMOVE_DIR.lower() : 
            for f in fs :      
                pf = os.path.join(p, f)       
                print('文件删除：path=%s, 文件=%s...' %(p, pf))
                del_file_obj(pf, IsDir=False)
            for d in ds :
                pd = os.path.join(p, d)
                print('目录删除1：path=%s, 目录=%s...' %(p, pd))
                err_info = del_file_obj(pd, IsDir=True)
                if err_info != '' :
                    print('异常：%s' %(err_info))
        else :
            for d in ds :
                if d.lower() == FILE_REMOVE_DIR.lower() :
                    pd = os.path.join(p, d)
                    print('目录删除2：path=%s, 目录=%s...' %(p, pd))
                    err_info = del_file_obj(pd, IsDir=True)
                    if err_info != '' :
                        print('异常：%s' %(err_info))
    
    print('del_dummy_physical结束.')            
    return


#从root下删除文件file
def del_file_dummy(root, file) :
    err_info = ''
    if not os.path.exists(root) or not os.path.exists(file) :
        return '目录或文件不存在。root=%s, file=%s.' %(root, file) 
    if file.lower().find(root.lower()) != 0 :
        return "文件和目录没有相关性。root=%s, file=%s." %(root, file)   
        
    dummy_dir = os.path.join(root, FILE_REMOVE_DIR)
    if not os.path.exists(dummy_dir) :
        try :
            os.mkdir(dummy_dir)
        except Exception as e :
            err_info = "创建dummy目录(%s)失败，原因：%s." %(dummy_dir, str(e))

    if err_info == '' :
        dummy_file = os.path.basename(file)
        dummy_file = os.path.join(dummy_dir, dummy_file)
        #print('尝试把文件(%s)移动到(%s)...' %(file, dummy_file))
        if file.lower() != dummy_file.lower() :
            dummy_file += '.tmp'    #让削刮器不处理
            try :
                os.rename(file, dummy_file)
            except Exception as e :
                err_info = "把文件(%s)移动到dummy(%s)失败，原因：%s, 尝试SHELL移动..." %(file, dummy_file, str(e))                
                print(err_info)
                try :
                    shutil.move(file, dummy_file)    
                    err_info = ''
                except Exception as e :
                    err_info = "SHELL把文件(%s)移动到dummy(%s)失败，原因：%s, 彻底失败." %(file, dummy_file, str(e))                

    return err_info

#把一个文件移动到下级目录，如指定的下级目录不存在则创建
def move_file_to_sub(file_name, sub_name='tmp') :
    if sub_name.strip() == '' :
        return
    if (not os.path.exists(file_name)) or (not os.path.isfile(file_name)) :
        return
    cur_dir = os.path.dirname(file_name)
    sub_dir = os.path.join(cur_dir, sub_name)
    err_info = ''
    if not os.path.exists(sub_dir) :
        try :
            os.mkdir(sub_dir)
        except Exception as e :
            err_info = "创建sub目录(%s)失败，原因：%s." %(sub_dir, str(e))
    if err_info == '' :
        sub_file = os.path.basename(file_name)
        sub_file = os.path.join(sub_dir, sub_file)
        try :
            os.rename(file_name, sub_file)
        except Exception as e :
            err_info = "把文件(%s)移动到sub(%s)失败，原因：%s, 尝试SHELL移动..." %(file_name, sub_file, str(e))                
            print(err_info)
            try :
                shutil.move(file_name, sub_file)    
                err_info = ''
            except Exception as e :
                err_info = "SHELL把文件(%s)移动到sub(%s)失败，原因：%s, 彻底失败." %(file_name, sub_file, str(e))                
    return err_info

#IsDir参数被废弃，由函数内部自动判断
def del_file_obj(path_name, IsDir=True) :
    err_info = del_file_obj_recycle(path_name)
    if err_info != '' :
        try :
            if os.path.exists(path_name) :
                if os.path.isdir(path_name) :
                    #os.rmdir(path_name)
                    shutil.rmtree(path_name)        #删除目录和目录下的所有文件和子目录
                else :
                    os.remove(path_name)
            err_info = ''
        except Exception as e :
            err_info = "删除文件系统对象(%s)失败，是否目录=%s，原因：%s。" %(path_name, IsDir, str(e))
    return err_info

#重命名，移动和规整函数
def file_rename(src : str, dest : str, ForceUpper : bool = True) -> str :
    err_info = ''
    #print('重命名处理，src=({}), dest=({})...'.format(src, dest))
    dir_name = os.path.dirname(dest)
    base_name = os.path.basename(dest)
    suitable_name = ''
    if src.upper() == dest.upper() :  #规整处理
        if os.path.isdir(src) :  #目录规整
            if ForceUpper :
                suitable_name = base_name.upper()
            else :
                suitable_name = dest
            suitable_name = os.path.join(dir_name, suitable_name)
        elif os.path.isfile(src) : #文件规整
            pure_name = os.path.splitext(base_name)[0]
            suffix = os.path.splitext(base_name)[1]
            if ForceUpper :
                suitable_name = pure_name.upper() + suffix.lower()
            else :
                suitable_name = pure_name + suffix.lower()
            suitable_name = os.path.join(dir_name, suitable_name)
            #print('suitalble name=%s...' %(suitable_name))
        if suitable_name != '' and suitable_name != src :
            tmp_name = src + RENAME_TMP_ADD
            try :
                os.rename(src, tmp_name)
                time.sleep(0.02)
                os.rename(tmp_name, suitable_name)
            except Exception as e :
                err_info = "规整重命名失败，原因：%s." %str(e)
    else :   #重命名或移动
        if os.path.isdir(src) : 
            if ForceUpper :
                suitable_name = dest.upper()  #目录名，全部大写
            else :
                suitable_name = dest
        elif os.path.isfile(src) :
            if ForceUpper :
                dir_name = os.path.dirname(dest)
                base_name = os.path.basename(dest)
                pure_name = os.path.splitext(base_name)[0]
                suffix = os.path.splitext(base_name)[1]
                suitable_name = pure_name.upper() + suffix.lower()
                suitable_name = os.path.join(dir_name, suitable_name)
            else :
                suitable_name = dest
        if suitable_name != '' : 
            try :
                os.rename(src, suitable_name)
            except Exception as e :
                err_info = "标准化重命名失败，原因：%s." %str(e)        
    return err_info            

def print_video_info() :
    FILES = ('Y:\\#临时\\鬼驱人.1981\\The.Beyond.1981.1080p.BluRay.x264.READ.NFO-CREEPSHOW.mkv', \
        'X:\\电视剧\\大侦探波洛\\第5季.S05\\Agatha.Christies.Poirot.S05E02.弱者的愤怒.1080p.BluRay.x264-YELLOWBiRD.mkv', \
        'X:\\电视剧\\摩登情爱\\第二季\\Modern.Love.2019.S02E01.1080p.WEB.H264-GLHF.mkv', \
        'Z:\\爱情\\婚姻故事.2019\\Marriage.Story.2019.BluRay.720p.x264.DTS-HDChina.mkv', \
        'Z:\\【导演】\\蒂姆·波顿\\蝙蝠侠归来.1992\\Batman.Returns.1992.2160p.BluRay.REMUX.HEVC.DTS-HD.MA.TrueHD.7.1.Atmos-FGT.mkv', )
    print('begin check...')
    for file in FILES :
        print('begin check file...')
        info = get_video_file_info(file)
        if info is not None :
            print('file=%s' %file)
            info.print()
            print('')
    return

def calc_video_resolution_ratio() :
    now_t = datetime.now()
    str_now = datetime.strftime(now_t, '%H-%M-%S') 
    out_file = open('视频分辨率统计' + str_now + '.txt', 'w+', encoding='utf-8')
    sys.stdout = out_file  #标准输出重定向至文件
    
    #HANDLE_DIRS = ('N:\\电视剧\\克拉克森的农场', 'N:\\电视剧\\大侦探波洛', 'N:\\电视剧\\摩登情爱\\第二季', )
    #HANDLE_DIRS = ('Z:\\', 'L:\\', 'N:\\电视剧', )
    HANDLE_DIRS = ('Z:\\爱情', )
    ratio_dict = dict()
    for root_dir in HANDLE_DIRS :
        print('开始检测根目录%s...' %root_dir)
        for p, ds, fs in os.walk(root_dir) :
            for f in fs :
                if f.lower().endswith('.mkv') or f.lower().endswith('.mp4') :
                    file_name = os.path.join(p, f)
                    print('检测文件%s...' %file_name)
                    info = get_video_file_info(file_name)
                    if info is not None and info.height > 0 and info.width > 0 :
                        scale = float(info.width / info.height)
                        final = "{:.2f}".format(scale)
                        ratio_str = str(int(info.height)) + '*' + str(int(info.width))
                        print('分辨率大小=%d*%d. 比例=%.2f%%. \n' %(info.height, info.width, scale))
                        font_size = info.get_video_font_size()
                        if font_size is not None :
                            str_font = '(' + str(font_size[0]) + ', ' + str(font_size[1]) + ')'
                            if str_font in ratio_dict :
                                found = False
                                info_list = ratio_dict[str_font]
                                for i in info_list :
                                    if i[0]==ratio_str :
                                        i[1] += 1
                                        found = True
                                        break
                                if not found :
                                    info_list.append( [ratio_str, 1] )
                            else :
                                ratio_dict[str_font] = [ [ratio_str, 1] ]
                        else :
                            print('异常：该视频无法进行字体分类。')

    print('\n打印分辨率的字体归类...')
    for key in ratio_dict :
        data_list = ratio_dict[key]
        count = 0
        for d in data_list :
            count += d[1]
        print('信息：字体大小=%s, 视频数量=%d.' %(key, count))
        for d in data_list :
            print('---分辨率=%s，视频数量=%d。' %(d[0], d[1]))

    return

def del_file_obj_recycle(path_name) :
    if not os.path.exists(path_name) :
        return '参数指定的路径不存在。'
    is_dir = os.path.isdir(path_name)
    err = ''
    cmd_line = 'Recycle.exe -f %s' %(path_name)     #d:\tool\comutil
    ret = subprocess.call(cmd_line, shell=True)
    if ret != 0 :
        err = '删除文件对象(%s)到回收站失败，code=%d。'  %(path_name, ret)
    return err

def check_low_quality_video() :
    now_t = datetime.now()
    str_now = datetime.strftime(now_t, '%H-%M-%S') 
    out_file = open('低分辨率统计' + str_now + '.txt', 'w+', encoding='utf-8')
    sys.stdout = out_file  #标准输出重定向至文件
    
    #HANDLE_DIRS = ('N:\\电视剧\\克拉克森的农场', 'N:\\电视剧\\大侦探波洛', 'N:\\电视剧\\摩登情爱\\第二季', )
    #HANDLE_DIRS = ('Z:\\', 'L:\\', 'N:\\电视剧', )
    HANDLE_DIRS = ('Y:\\', )
    for root_dir in HANDLE_DIRS :
        print_low_quality_video(root_dir)
    return

def test_dir_name() :
    target_dir = 'Y:\\MUSES\\华语女艺人\\千百惠\\清新甜美的歌喉 千百惠《珍惜今昔·成名金曲》[WAV]'
    src_obj = 'Y:\\MUSES\\华语女艺人\\千百惠\\清新甜美的歌喉 千百惠《珍惜今昔·成名金曲》CD1[WAV]'
    base_name = os.path.basename(src_obj)
    path_new = os.path.join(target_dir, base_name)
    print(path_new)
    return  

#print_video_info()
#calc_video_resolution_ratio()
#check_low_quality_video()

#test_dir_name()