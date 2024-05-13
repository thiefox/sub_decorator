import os
import re

from datetime import datetime

from com_utils import FileOpWrapper
from com_utils.general_info import STANDARD_EPISODE_FORMAT
from com_utils import TaskManager

import subtitle.defs as defs
from subtitle.sub_filer import sub_filer
from subtitle.srt_sub_filer import srt_sub_filer
from subtitle.ass_sub_filer import ass_sub_filer

#载入字幕文件
def load_sub(file_name : str) -> sub_filer :
    if not os.path.exists(file_name) or not os.path.isfile(file_name) :
        return None
    filer = None
    suffix = os.path.splitext(file_name)[1].lower()
    if suffix == '.srt' :
        filer = srt_sub_filer()
        if not filer.load(file_name) :
            filer = None
            print('异常：载入{}字幕{}失败。'.format(suffix, file_name))
    elif suffix == '.ass' or suffix == '.ssa' :
        filer = ass_sub_filer()
        if not filer.load(file_name) :
            filer = None
            print('异常：载入{}字幕{}失败。'.format(suffix, file_name))
    else :
        print('异常：不支持的字幕格式{}'.format(file_name))
    if filer is not None :
        pass
    return filer

#强制转换为ass_filer
def force_2_ass_filer(filer : sub_filer) -> ass_sub_filer :
    ass_filer = None
    if isinstance(filer, ass_sub_filer) :
        ass_filer = filer
    elif isinstance(filer, srt_sub_filer) :
        ass_filer = ass_sub_filer()
        print('开始拷贝srt对象到ass对象...')
        ass_filer.copy_from(filer)
        print('拷贝srt对象到ass对象完成。')
    else :
        assert(False)
    return ass_filer

#检测视频文件和字幕文件命名是否匹配
def is_matched_sub(video_file : str, sub_file : str) -> bool :
    pure_video = os.path.basename(video_file)
    pure_sub = os.path.basename(sub_file)
    video_name = os.path.splitext(pure_video)[0]
    matched = pure_sub.lower().find(video_name.lower()) == 0

    video_left = os.path.splitext(video_file)[0]
    sub_suffix = os.path.splitext(sub_file)[1]
    unique_sub = video_left + sub_suffix
    uniqued = os.path.exists(unique_sub)
    if uniqued :
        return matched
    else :
        return False

#把电影目录下的字幕文件重命名为和视频文件匹配
#如已存在同名的标准字幕文件，则重命名为.T1.suffix格式
def sync_sub_movie(video_file : str) -> int :
    SUB_FILE_MIDDLE_FLAG = '.T'
    dir_name = os.path.dirname(video_file)
    base_name = os.path.basename(video_file)
    pure_name = os.path.splitext(base_name)[0]  #视频文件名，不含后缀
    count = 0
    videos = FileOpWrapper.get_video_files(dir_name, only_cur=True)
    if len(videos) > 1 :        #异常：该目录下有多个视频文件
        print('异常：目录{}下有多个电影视频文件，字幕文件标准化命名失败。'.format(dir_name))
        return -1
    subs = FileOpWrapper.get_type_files(dir_name, defs.SUB_FILE_TYPE, only_cur=True)    
    for sub in subs :
        if is_matched_sub(video_file, sub) :    #已经是标准命名字幕
            continue
        if sub_filer.is_bigb_sub(sub) :                   #bigb系列字幕
            continue
        suffix = os.path.splitext(sub)[1].lower()
        new_name = pure_name + suffix
        new_name = os.path.join(dir_name, new_name)
        if not os.path.exists(new_name) :
            os.rename(sub, new_name)
        else :
            i = 1
            while True :
                new_name = pure_name + SUB_FILE_MIDDLE_FLAG + str(i) + suffix
                new_name = os.path.join(dir_name, new_name)
                if not os.path.exists(new_name) :
                    os.rename(sub, new_name)
                    break
                else :
                    i += 1
        count += 1
    return count

#把跟该视频文件在同一目录下的字幕文件调整为同名
#返回<0为异常
def sync_sub_tv(video_file : str) -> int : 
    series_info = re.search(STANDARD_EPISODE_FORMAT, video_file, re.I) 
    if series_info is None :  #从视频文件萃取到SXXEXX信息
        print("异常：视频文件{}无法萃取出季集信息！".format(video_file))
        return -1     
    dir_name = os.path.dirname(video_file)
    base_name = os.path.basename(video_file)
    pure_name = os.path.splitext(base_name)[0]  #视频文件名，不含后缀

    si_upper = series_info.group().upper()
    subs = FileOpWrapper.get_type_files(dir_name, defs.SUB_FILE_TYPE, only_cur=True)
    count = 0
    for sub in subs :       #字幕文件遍历
        if is_matched_sub(video_file, sub) :        #已匹配的字幕
            continue
        if sub_filer.is_bigb_sub(sub) :
            continue
        
        file = os.path.split(sub)[1].upper()
        index = file.find(si_upper)
        if index >= 0 : #找到对应季集信息的字幕
            suffix = os.path.splitext(sub)[1].lower()
            new_name = pure_name + suffix
            new_name = os.path.join(dir_name, new_name)
            if not os.path.exists(new_name) :  #没有重名的字幕文件
                os.rename(sub, new_name)
                count += 1   
            else :
                print("异常：已有和剧集视频同名的字幕文件，{}被忽略。".format(file))
    return count

#字幕文件预处理
#如video_file目录下只有video_file一个视频文件，则把非bigb字幕文件（可能有多个）命名成和视频文件同名。
#如video_file目录下有多个视频文件，则检测video_file是否为SXXEXX格式，如是，则查找含有同季同集信息的字幕文件命名成和视频文件同名。
def pretreatment_sub_file(video_file : str) :
    print('开始视频{}的字幕文件预处理...'.format(video_file))
    IS_MOVIE = True
    cur_dir = os.path.dirname(video_file)
    cur_file = os.path.basename(video_file)
    videos = FileOpWrapper.get_video_files(cur_dir, only_cur=True)
    if len(videos) > 1 :            #该目录下有多个视频文件
        IS_MOVIE = False
    else :
        series_info = re.search(STANDARD_EPISODE_FORMAT, cur_file, re.I) 
        if series_info is not None :
            #series_num = series_info.group()
            IS_MOVIE = False
    if IS_MOVIE :
        print('视频文件类型=电影...')
        sync_sub_movie(video_file)
    else :
        print('目录下有{}个视频文件，按剧集处理...'.format(len(videos)))
        sync_sub_tv(video_file)
    print('字幕文件预处理完成。')
    return

#取得path_file文件目录下所有原始字幕文件
#不包括bigb系列字幕
def get_all_subs(path_file : str, ALL_SUB = False) -> list :
    sub_files = list()
    dir_name = os.path.dirname(path_file)
    base_name = os.path.basename(path_file)
    pure_name = os.path.splitext(base_name)[0]
    files = FileOpWrapper.get_type_files(dir_name, defs.REBUILD_SUB_FILE_TYPE, only_cur=True)
    for f in files :
        if sub_filer.is_bigb_sub(f) :
            continue
        if ALL_SUB :
            sub_files.append(f)
        else :
            sub_base = os.path.basename(f)
            if sub_base.lower().find(pure_name.lower()) >= 0 :
                sub_files.append(f)
    return sub_files

#载入所有的字幕文件对象
def load_all_subs(path_file : str, ALL_SUB = False) -> list :
    sub_files = get_all_subs(path_file, ALL_SUB)
    filers = list()
    for sf in sub_files :
        filer = load_sub(sf)
        if filer is not None :
            filers.append(filer)
    return filers

#取得一个视频文件质量最好的字幕文件(双语>单语, ass>ssa>srt)
def get_best_filer(filers : list) -> sub_filer :
    best = None
    for filer in filers :
        if best is None :
            best = filer
        elif not best.get_lang_mode().is_better(filer.get_lang_mode()) :
            best = filer
    if best is not None :
        print('找到最优字幕文件={}。'.format(best.get_file_name()))
        best.get_lang_mode().print()
    return best

#尝试合成双语字幕
#base_filer：基准的单语字幕对象
def try_merge(base_filer : sub_filer, all_filers : list) -> bool :
    base_lm = base_filer.get_lang_mode()
    assert(not base_lm.is_double())
    for filer in all_filers :
        if base_filer.is_same(filer) :
            continue
        cur_lm = filer.get_lang_mode()
        #cur_lm = defs.SUB_EVENT_LANG_MODE()
        if not cur_lm.is_double() and cur_lm.first_lang != base_lm.first_lang :
            if base_filer.outer_merge(filer) :  #成功进行了双语合并
                return True
    return False

#字幕生成任务
class sub_generate_task(TaskManager.Task_Impl_Base) :
    def __init__(self) :
        super().__init__()
        self.IS_TVSHOW_DIR = False
        self.FORCE_REBUILD = False
        return
    def get_log_name(self) :
        return '字幕生成EX'
    def is_deal_item(self, path_name, is_dir) :
        deal = False
        if not is_dir :
            if FileOpWrapper.is_video_file(path_name) :
                deal = True
        return deal
    def deal_with(self, path_name, is_dir) :
        if not self.is_deal_item(path_name, is_dir) :
            return 0
        self.deal_a_video(path_name)
        return 1
    def deal_a_video(self, path_file : str) :
        MAX_SECONDS = 3
        t_begin = datetime.now()
        print('\ntime={}, 开始处理视频文件{}...'.format(t_begin.strftime('%H:%M:%S'), path_file))
        print('开始字幕预处理...')
        #字幕文件预处理
        pretreatment_sub_file(path_file)
        print('字幕预处理完成.')
        #获取质量最高的字幕文件
        t_end = datetime.now()
        if (t_end - t_begin).seconds > MAX_SECONDS :
            print('异常：字幕预处理时间过长={}秒'.format((t_end-t_begin).seconds))
        all_filers = load_all_subs(path_file, ALL_SUB = not self.IS_TVSHOW_DIR)
        best_filer = get_best_filer(all_filers)
        t_end = datetime.now()
        if (t_end - t_begin).seconds > MAX_SECONDS :
            print('异常：查找最优字幕处理时间过长={}秒'.format((t_end-t_begin).seconds))        
        if best_filer is None :
            print('无法找到匹配的字幕。')
        else :
            print('找到匹配的字幕={}'.format(best_filer.get_file_name()))
            if not best_filer.get_lang_mode().is_double() :       #单语字幕
                print('尝试合并外部双语文件...')
                merged = try_merge(best_filer, all_filers)
                print('合并外部双语文件完成，结果={}'.format(merged))
                t_end = datetime.now()
                if (t_end - t_begin).seconds > MAX_SECONDS :
                    print('异常：合并双语字幕处理时间过长={}秒'.format((t_end-t_begin).seconds))
            #以ass格式保存bigb系列字幕
            print('开始生成bigb系列字幕...')
            ass_filer = force_2_ass_filer(best_filer)
            t_end = datetime.now()
            if (t_end - t_begin).seconds > MAX_SECONDS :
                print('异常：强制切换到ASS模式处理时间过长={}秒'.format((t_end-t_begin).seconds))
            if ass_filer is not None :
                print('切换到ass模式完成。')
                assert(isinstance(ass_filer, ass_sub_filer))
                ass_filer.attach_video(path_file)
                ass_filer.save_bigb()
                print('生成bigb系列ass字幕完成。')
                t_end = datetime.now()
                if (t_end - t_begin).seconds > MAX_SECONDS :
                    print('异常：输出bigb字幕处理时间过长={}秒'.format((t_end-t_begin).seconds))
            else :
                print('异常：字幕{}无法切换到ass模式。'.format(best_filer.get_file_name()))
        t_end = datetime.now()
        if (t_end - t_begin).seconds > MAX_SECONDS :
            print('异常：视频{}的处理时间过长={}秒。'.format(path_file, (t_end - t_begin).seconds))
        return