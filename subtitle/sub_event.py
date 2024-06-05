from __future__ import annotations
from enum import Enum, unique

from datetime import datetime

import subtitle.defs as defs
from com_utils import StrHandler

class sub_event(object) :
    #ASS_DEFAULT_MAIN_STYLE = 'BIGBM'
    #ASS_DEFAULT_SECONDARY_STYLE = 'BIGBS'
    #ASS_EVENT_FORMAT = 'Dialogue: 0,0:02:38.60,0:02:40.48,Default,,0000,0000,0000,,上面印着一只鹰的\N{\fntahoma\fs10\1c&H0080FF&}with the eagle\non top and...{\r}'    
    #SRC_EVENT_FORMAT = 3
    #    00:02:19,720 --> 00:02:21,630
    #    {\fnMicrosoft YaHei\fs17\bord1\shad1\b0}给我来点糖{\r}
    #    {\fnTahoma\fs8\bord1\shad1\1c&HC2E0EC&\b0}Sonny,  you wanna hit me up with some syrup?{\r}
    #中文推荐字体：
    #英文推荐字体：
    DOUBLE_ENG_FORMAT_ARIAL = '{\\fnarial\\fs14\\c&H62A8EB&}'
    DOUBLE_ENG_FORMAT_YAHEI = '{\\fn微软雅黑\\fs14\\c&H62A8EB&}'
    DOUBLE_ENG_FORMAT_TAHOMA = '{\\fntahoma\\fs14\\c&H62A8EB&}'
    #begin, end, chs_text, controler, eng_text
    ASS_EVENT_DOUBLE_FORMAT_EX = 'Dialogue: 0,%s,%s,%s,,%s,,%s\\N{\\r%s}%s'
    ASS_EVENT_SINGLE_FORMAT = 'Dialogue: 0,%s,%s,%s,,%s,,%s'
    SSA_EVENT_MAIN_STYLE_YAHEI = '{\\1c&HFFFFFF&}{\\fn微软雅黑\\fs22}'
    SSA_EVENT_MAIN_STYLE_ARIAL = '{\\1c&HFFFFFF&}{\\fnarial\\fs22}'
    SSA_EVENT_SECONDARY_STYLE_ARIAL = '{\\1c&H62A8EB&}{\\fnarial\\fs13}'

    SRT_TIME_SPLITTER = ' --> '
    #CONTROLERS = ( ('{', '}'), ('<', '>'), )
    CONTROLER_DICT = {'{': '}', '<': '>', }
    #SRT_TIME_FORMAT = (r'(\d{1,2}:\d{1,2}:\d{1,2},\d{1,3})', r'(\d{1,2}:\d{1,2}:\d{1,2}:\d{1,3})', r'(\d{1,2}:\d{1,2}:\d{1,2}.\d{1,3})', )
    ASS_TIME_FORMAT = r'(\d{1}:\d{2}:\d{2}.\d{1,3})'
    ASS_EFFECT_SUB_FLAG = r'(\\pos\(\d{1,3},\d{1,3}\)\\)'
    SRT_SUB_DIFF_LANG_SPLITTERS = (' - ', )
    
    #ASS_EVENT_METADATA_SPLITTER = ','
    #ASS_EVENT_METADATA_SPLITTER_COUNT = 9          #出现9个英文逗号后，为ASS字幕正文

    def __init__(self) :
        self.raw_lines = list()      #原始数据(字符串列表)
        self.begin_time = datetime.min
        self.end_time = datetime.min
        self.main_txt = ''          #主字幕文本
        self.secondary_txt = ''     #次字幕文本（双语字幕时有效）
        return
    def get_mt(self) -> str :
        return self.main_txt
    def get_st(self) -> str :
        return self.secondary_txt
    def has_mt(self) -> bool :
        return self.get_mt() != ''
    def has_st(self) -> bool :
        return self.get_st() != ''
    #主字幕赋值
    def set_mt(self, main : str) :
        self.main_txt = main
    #次字幕赋值
    def set_st(self, secondary : str) :
        self.secondary_txt = secondary
    #附加主字幕的文本
    def append_mt(self, txt : str, SPLIT = ' ') :
        if self.has_mt() :      #已有数据
            self.main_txt += SPLIT + txt
        else :  #没有数据
            self.main_txt = txt
        return
    #附加次字幕的文本
    def append_st(self, txt : str, SPLIT = ' ') : 
        if self.has_st() :
            self.secondary_txt += SPLIT + txt
        else :
            self.secondary_txt = txt
        return
    #是否单语事件
    def is_single(self) -> bool :
        return self.has_mt() and not self.has_st()
    #是否双语事件
    def is_double(self) -> bool :
        return self.has_mt() and self.has_st()
    #私有函数，切换主字幕和次字幕
    def _switch_txt(self) :
        tmp = self.main_txt
        self.main_txt = self.secondary_txt
        self.secondary_txt = tmp
        return
    #把中文字幕切换为主字幕
    def switch_chs_2_main(self) :
        if self.is_double() :
            if self.is_secondary_ch() :
                self._switch_txt()
        return
    #强制切换主次字幕
    #双语事件直接切换
    #单语事件，level=1直接切换，level=0且主字幕非中文时切换
    def switch_force(self, level : int = 0 ) :
        if self.is_double() :
            self._switch_txt()
        else :
            if level == 1 :
                self._switch_txt()
            elif level == 0 and not self.is_main_ch() :
                self._switch_txt()
        return
    #最宽松匹配：有一个中文字符，即认为是中文
    def is_main_ch(self) -> bool :
        return StrHandler.get_zh_percent(self.get_mt()) > 0
    def is_secondary_ch(self) -> bool :
        return StrHandler.get_zh_percent(self.get_st()) > 0
    def is_main_eng(self) -> bool :
        return StrHandler.is_lang_eng(self.get_mt())
    def is_secondary_eng(self) -> bool :
        return StrHandler.is_lang_eng(self.get_st())
    def same_lang_as_main(self, txt : str) -> bool :
        same = False
        if self.is_main_ch() and StrHandler.get_zh_percent(txt) > 0 :
            same = True
        else :
            same = StrHandler.is_zh_or_eng(self.get_mt()) == StrHandler.is_zh_or_eng(txt)
        return same
    def same_lang_as_secondary(self, txt : str) -> bool :
        same = False
        if self.is_secondary_ch() and StrHandler.get_zh_percent(txt) > 0 :
            same = True
        else :
            same = StrHandler.is_zh_or_eng(self.get_st()) == StrHandler.is_zh_or_eng(txt)
        return same    
    #繁体转换到简体
    def cht_2_chs(self) -> bool :
        if self.is_effect() :
            return False
        updated = False
        if self.is_main_ch() :
            temp = StrHandler.cht_to_chs(self.main_txt)
            if temp != self.main_txt :
                self.main_txt = temp
                updated = True
        if self.is_secondary_ch() :
            temp = StrHandler.cht_to_chs(self.secondary_txt)
            if temp != self.secondary_txt :
                self.secondary_txt = temp
                updated = True
        return updated
    #检测事件的时间戳有效
    def time_valid(self) -> bool :
        return self.begin_time != datetime.min and self.end_time >= self.begin_time
    def set_time_info(self, begin : datetime, end : datetime) :
        self.begin_time = begin
        self.end_time = end
        return
    #子类重载函数
    #检测事件的文本是否有效
    def txt_valid(self) -> bool :
        return self.has_mt()
    #子类重载函数
    #是否特效事件
    def is_effect(self) -> bool :
        return False
    #子类重载函数
    #分析事件的语言构成
    def analysis(self) -> defs.SUB_EVENT_LANG_MODE :
        return defs.SUB_EVENT_LANG_MODE()
    def raw_valid(self) -> bool :
        return self.time_valid() and len(self.raw_lines) > 0 
    def valid(self) -> bool :
        return self.time_valid() and self.txt_valid()

    def get_raw(self) -> list :
        return self.raw_lines
    def set_raw(self, lines : list) :
        self.raw_lines = lines
        return
    def is_txt_event(self) -> bool :
        return True

    #比较两个事件是否属于同一个时间段，默认允许误差为1秒
    #precison==1，允许误差100毫秒
    #precison==2，允许误差10毫秒
    def _is_sub_same_time(self, other : sub_event, PRECISION : defs.TIME_PRECISION) -> bool :
        begin_samed = end_samed = False
        begin_delta = self.begin_time - other.begin_time
        end_delta = self.end_time - other.end_time
        if PRECISION == defs.TIME_PRECISION.EXACT :     #完全匹配
            begin_samed = self.begin_time == other.begin_time
            end_samed = self.end_time == other.end_time
        elif PRECISION == defs.TIME_PRECISION.MILLSECOND_10 :       #匹配到10毫秒
            begin_samed = abs(begin_delta.total_seconds()) <= 0.01
            end_samed = abs(end_delta.total_seconds()) <= 0.01
            #begin_samed = (begin_delta.days == 0) and (begin_delta.seconds == 0) and (begin_delta.microseconds <= 1 * 1000)
            #end_samed = (end_delta.days == 0) and (end_delta.seconds == 0) and (end_delta.microseconds <= 1 * 1000)
        elif PRECISION == defs.TIME_PRECISION.MILLSECOND_100 :      #匹配到100毫秒
            begin_samed = abs(begin_delta.total_seconds()) <= 0.1
            end_samed = abs(end_delta.total_seconds()) <= 0.1
            #begin_samed = (begin_delta.days == 0) and (begin_delta.seconds == 0) and (begin_delta.microseconds <= 10 * 1000)
            #end_samed = (end_delta.days == 0) and (end_delta.seconds == 0) and (end_delta.microseconds <= 10 * 1000)
        elif PRECISION == defs.TIME_PRECISION.SECOND :              #匹配到1秒
            begin_samed = abs(begin_delta.total_seconds()) <= 1
            end_samed = abs(end_delta.total_seconds()) <= 1
        return begin_samed and end_samed
    #比较两个时间轴是否相同
    def is_same_time(self, other : sub_event, PRECISION : defs.TIME_PRECISION) -> bool :
        return self._is_sub_same_time(other, PRECISION)

    #输出srt格式的时间区间
    #srt_time_format = '00:07:38,250 --> 00:07:39,900'    
    def get_time_interval_str(self) -> str :
        SRT_TIME_FORMAT = '%H:%M:%S,%f'
        SRT_MILLSECOND_HOLDERS = 3
        SRT_CONNECTOR = ' --> '
        ASS_TIME_FORMAT = '%H:%M:%S.%f'
        ASS_MILLSECOND_HOLDERS = 2
        ASS_CONNECTOR = ','
        info = ''
        if self.time_valid() :
            info = self.begin_time.strftime(SRT_TIME_FORMAT)[:-SRT_MILLSECOND_HOLDERS]
            info += SRT_CONNECTOR
            info += self.end_time.strftime(SRT_TIME_FORMAT)[:-SRT_MILLSECOND_HOLDERS]
        return info

    #打印时间轴，格式为srt时间轴格式
    def print_time_axis(self) -> str:
        return self.get_time_interval_str()

    #打印字幕文本
    def print_txt(self) -> str :
        info = ''
        if self.main_txt != '' :
            info = 'main_txt={}'.format(self.main_txt)
        if self.secondary_txt != '' :
            info += '\n'
            info += 'secondary_txt={}'.format(self.secondary_txt)
        return info
    #时间数据字符串标准化
    def time_standard(input : str) -> str :
        output = input.replace(' ', '')
        REPLACE_ITEMS = (('，', ','), ('：', ':'), ('。', '.'), )
        for RI in REPLACE_ITEMS :
            output = output.replace(RI[0], RI[1])
        return output

    #字符串时间转化为时间对象
    def time_info_2_datetime(str_time : str) -> datetime :
        str_time = sub_event.time_standard(str_time)

        SPLITTERS = ('.', ',', ':', )   #毫秒分隔符列表
        time_info = None

        for sp in SPLITTERS :
            index = str_time.rfind(sp)
            if index >= 0 :     #找到分隔符
                str_format = '%H:%M:%S' + sp + '%f'
                try :
                    time_info = datetime.strptime(str_time, str_format)
                    break
                except Exception as e :
                    print('异常：时间解析异常1，输入=(%s)，原因: (%s).' %(str_time, str(e)))
                    assert(False)
                    return None
                
        if time_info is None :      #没有毫秒级数据
            try :
                time_info = datetime.strptime(str_time, '%H:%M:%S')
            except Exception as e :
                print('异常：时间解析异常2，输入=(%s)，原因: (%s).' %(str_time, str(e)))
                assert(False)
                return None
        return time_info

    #检测在events中是否存在跟当前event时间戳匹配的事件
    #找到返回events中的匹配事件，未找到返回None
    def is_exist(self, events : list, PRECISION : defs.TIME_PRECISION) -> sub_event :
        for e in events :
            #e = sub_event(e)
            if e.is_txt_event() and self.is_same_time(e, PRECISION) :
                return e
        return None

    def print(self) :
        print('time_axis={}.'.format(self.print_time_axis()))
        print(self.print_txt())
        if len(self.raw_lines) > 0 :
            print('raw_data=')
            for line in self.raw_lines :
                print(line)
        return

    def get_time_begin(self) -> datetime :
        return self.begin_time
    #检测两个事件的主字幕是否不同的语种
    def is_main_diff(self, another : sub_event) -> bool :
        return not self.same_lang_as_main(another.get_mt())
    #自动侦测两个事件的语言进行合并处理
    def merge_with_detect(self, another : sub_event) -> bool :
        failed = False
        if self.is_single() and another.is_single() :       #两个都是单语
            if self.same_lang_as_main(another.get_mt()) :   #语言相同
                self.append_mt(another.get_mt())
            else :
                self.set_st(another.get_mt())
        elif self.is_single() or another.is_single() :      #一个单语，一个双语
            if self.is_single() :
                if self.same_lang_as_main(another.get_mt()) :
                    self.append_mt(another.get_mt())
                    self.set_st(another.get_st())
                elif self.same_lang_as_main(another.get_st()) :
                    self.append_mt(another.get_st())
                    self.set_st(another.get_mt())
                else :
                    print('异常，无法合并1，基准事件：{}, 合并事件：{}。'.format(self.print_txt(), another.print_txt()))
                    failed = True
            else :
                if self.same_lang_as_main(another.get_mt()) :
                    self.append_mt(another.get_mt())
                elif self.same_lang_as_secondary(another.get_mt()) :
                    self.append_st(another.get_st())
                else :
                    print('异常，无法合并2，基准事件：{}, 合并事件：{}。'.format(self.print_txt(), another.print_txt()))
                    failed = True
        else :  #两个都是双语
            if self.same_lang_as_main(another.get_mt()) and self.same_lang_as_secondary(another.get_st()) :
                self.append_mt(another.get_mt())
                self.append_st(another.get_st())
            elif self.same_lang_as_main(another.get_st()) and self.same_lang_as_secondary(another.get_mt()) :
                self.append_mt(another.get_st())
                self.append_st(another.get_mt())
            else :
                print('异常，无法合并3，基准事件：{}, 合并事件：{}。'.format(self.print_txt(), another.print_txt()))
                failed = True
        return not failed
    #根据给定的模式进行合并处理
    def merge_with_mode(self, another : sub_event, MODE : defs.SUB_MERGER_MODE) -> bool :
        failed = False
        if MODE == defs.SUB_MERGER_MODE.MAIN_TO_MAIN :
            self.append_mt(another.get_mt())
        elif MODE == defs.SUB_MERGER_MODE.MAIN_TO_SECONDARY :
            self.append_st(another.get_mt())
        elif MODE == defs.SUB_MERGER_MODE.BOTH :
            self.append_mt(another.get_mt())
            self.append_st(another.get_st())
        elif MODE == defs.SUB_MERGER_MODE.BOTH_REVERSE :
            self.append_mt(another.get_st())
            self.append_st(another.get_mt())
        else :
            print('异常，无法合并4，模式={}，基准事件：{}, 合并事件：{}。'.format(MODE, self.print_txt(), another.print_txt()))
            failed = True
        return not failed
    #合并另一个事件
    def merge_from(self, another : sub_event, MODE : defs.SUB_MERGER_MODE) -> bool :
        if MODE == defs.SUB_MERGER_MODE.UNKNOWN :
            result = self.merge_with_detect(another)
        else :
            result = self.merge_with_mode(another, MODE)
        return result
