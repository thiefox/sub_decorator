from __future__ import annotations
from enum import Enum, unique
import os
import configparser

from datetime import datetime

from com_utils import StrHandler

SUB_FILE_TYPE = ('.ass', '.ssa', '.srt', '.sup', '.idx', '.sub', )
REBUILD_SUB_FILE_TYPE = ('.ass', '.ssa', '.srt', )

#字幕合并模式
@unique
class SUB_MERGER_MODE(Enum) :
    UNKNOWN = 0
    MAIN_TO_MAIN = 1,           #单语合并
    MAIN_TO_SECONDARY = 2,      #单语变双语
    BOTH = 3,                   #双语合并（主对主，次对次）
    BOTH_REVERSE = 4            #双语合并（主对次，次对主）

#时间轴匹配精度
@unique
class TIME_PRECISION(Enum) :
    EXACT = 0,              #完全匹配
    MILLSECOND_10 = 1,      #精确到10毫秒
    MILLSECOND_100 = 2,     #精确到100毫秒
    SECOND = 3              #精确到1000毫秒（1秒）

#字幕文件格式
@unique
class SUB_FORMAT(Enum) :
    def __new__(sl, suffix : str, eval : int):
        obj = object.__new__(sl)
        obj.suffix = suffix
        obj.eval = eval
        return obj
    ERROR = 'ERROR', -1
    UNKNOWN = 'UNKNOWN', 0
    SRT = 'SRT', 1
    SSA = 'SSA', 2
    ASS = 'ASS', 3
    IGNORE = 'IGNORE', 100

    def get_int(self) -> int :
        return self.eval
    def get_suffix(self) -> str :
        return self.suffix             #same as self.value[0]
    def _get_priority(suffix : str) -> int :
        priority = 0
        suffix = suffix.upper()
        if suffix == 'SRT' :
            priority = 10
        elif suffix == 'SSA' :
            priority = 20
        elif suffix == 'ASS' :
            priority = 30
        return priority
    #取得字幕文件格式的优先级
    def get_priority(self) -> int :
        return SUB_FORMAT._get_priority(self.get_suffix())
    def from_int(value : int) -> SUB_FORMAT :
        format = SUB_FORMAT.UNKNOWN
        for _, member in SUB_FORMAT.__members__.items() :
            if member.get_int() == value :
                format = member
                break
        return format
    def from_name(name : str) -> SUB_FORMAT :
        if name[0] == '.' :
            name = name[1:]
        format = SUB_FORMAT.UNKNOWN
        for _, member in SUB_FORMAT.__members__.items() : 
            if member.get_suffix() == name.upper() :
                format = member
                break
        return format
    #取得字幕文件格式的优先级，ASS > SSA > SRT
    def get_sub_priority(name : str) -> int :
        if len(name) > 0 :
            if name[0] == '.' :
                name = name[1:]
            elif len(name) == 3 :   #标准后缀
                pass
            else :  #检测是否文件名格式
                name = os.path.splitext(name)[-1]
                if len(name) > 0 :  #萃取到后缀，去.
                    name = name[1:]
        return SUB_FORMAT.get_priority(name)

#ASS字幕字体风格分类
@unique
class ASS_FONT_STYLE(Enum) :
    DEFAULT = 0, 'default'          #默认风格
    MAIN = 1, 'BIGBM'               #主字幕风格
    SECOND = 2, 'BIGBS'             #次字幕风格
    def __new__(afs, eval : int, desc : str):
        obj = object.__new__(afs)
        obj.eval = eval
        obj.desc = desc
        return obj
    def get_int(self) -> int :
        return self.eval
    def get_name(self) -> str :
        return self.desc
    def from_int(value : int) -> ASS_FONT_STYLE :
        style = ASS_FONT_STYLE.DEFAULT
        for _, member in ASS_FONT_STYLE.__members__.items():
            if member.get_int() == value :
                style = member
                break
        return style

#字幕语言枚举
@unique
class SUB_LANG(Enum) :
    EMPTY = -2, ''
    ERROR = -1, '异常'      #检测过
    UNKNOWN = 0, '未知'     #未检测过
    CHINESE = 1, '中文'
    CHT = 2, '中文繁体'
    ENGLISH = 3, '英文'
    JAPANESE = 4, '日文'
    KOREAN = 5, '韩文'
    OTHER_LANG = 1000, '其它语言'
    def __new__(sl, eval : int, desc : str):
        obj = object.__new__(sl)
        obj.eval = eval
        obj.desc = desc
        return obj
    def get_int(self) -> int :
        return self.eval
    def get_name(self) -> str :
        return self.desc
    def error(self) -> bool :
        return self == SUB_LANG.ERROR
    def valid(self) -> bool :
        return self != SUB_LANG.UNKNOWN and self != SUB_LANG.EMPTY and not self.error()
    def from_int(value : int) -> SUB_LANG :
        lang = SUB_LANG.UNKNOWN
        for _, member in SUB_LANG.__members__.items():
            if member.get_int() == value :
                lang = member
                break
        return lang
    #检测文本的语言信息
    def check(txt : str) -> SUB_LANG :
        lang = SUB_LANG.UNKNOWN
        txt = txt.strip()
        if len(txt) == 0 :
            return SUB_LANG.EMPTY
        if StrHandler.is_lang_zh(txt) :
            lang = SUB_LANG.CHINESE
        elif StrHandler.is_lang_eng(txt) :
            lang = SUB_LANG.ENGLISH
        elif StrHandler.is_contains_jap(txt) :
            lang = SUB_LANG.JAPANESE
        elif StrHandler.is_contains_korean(txt) :
            lang = SUB_LANG.KOREAN
        else :
            lang = SUB_LANG.OTHER_LANG
        return lang

#字幕的事件语言模式
class SUB_EVENT_LANG_MODE(object):
    def __init__(self) -> None:
        super().__init__()
        self.path_file = ''         #字幕文件名
        #self.format = SUB_FORMAT.UNKNOWN        #字幕文件格式(ass/ssa/srt)
        self.first_lang = SUB_LANG.UNKNOWN     #字幕第一语言（如双语字幕，则为事件的第一个语言）
        self.second_lang = SUB_LANG.UNKNOWN    #字幕第二语言（单语字幕忽略）
        self.mixed = True       #双语是否为混合模式（一个事件内包含了两种语言）
        self.spiral = False     #双语是否为螺旋分离
        self.time_match_rate = 0.0      #分离双语的时间轴匹配率（时间轴两两相同的事件数/有效文本事件数）
        return
    def __eq__(self, other) :
        if isinstance(other, self.__class__) :
            equal = self.first_lang == other.first_lang and self.second_lang == other.second_lang \
                and self.mixed == other.mixed and self.spiral == other.spiral
            return equal
        else:
            return False
    def __hash__(self):
        return hash((self.first_lang, self.second_lang, self.mixed))

    def lang_equal(self, other : SUB_EVENT_LANG_MODE) -> bool :
        equal = False
        equal = self.first_lang == other.first_lang and self.second_lang == other.second_lang \
            and self.mixed == other.mixed and self.spiral == other.spiral
        return equal
    def print(self) :
        if len(self.path_file) > 0 :
            print('字幕文件={}'.format(self.path_file))
        print('主字幕语言={}'.format(self.first_lang))
        print('次字幕语言={}'.format(self.second_lang))
        if self.is_double() :
            print('混合双语模式={}'.format(self.mixed))
            if not self.is_mixed() :
                print('螺旋分离模式={}'.format(self.spiral))
                print('双语时间轴匹配率={}'.format(self.time_match_rate))
        return
    def set_no_second(self) :
        self.second_lang = SUB_LANG.EMPTY
        return
    def reset_inner(self) :
        self.first_lang = SUB_LANG.UNKNOWN
        self.second_lang = SUB_LANG.UNKNOWN
        self.mixed = True
        self.spiral = False
        self.time_match_rate = 0.0
    #从事件的语言模式复制
    def copy_from_event(self, event_lm : SUB_EVENT_LANG_MODE) :
        self.first_lang = event_lm.first_lang
        self.second_lang = event_lm.second_lang
        self.mixed = True
        return
    def get_format_priority(self) -> int :
        suffix = os.path.splitext(self.path_file)[1]
        sub_format = SUB_FORMAT(SUB_FORMAT.from_name(suffix))
        return sub_format.get_priority()
    #比较self和other的字幕质量
    #返回True, self >= other。返回False，self < other
    def is_better(self, other : SUB_EVENT_LANG_MODE) -> bool :
        if self.is_double() :
            if other.is_double() :
                if self.get_format_priority() >= other.get_format_priority() :
                    return True
                else :
                    return False
            else :
                return True
        else :
            if other.is_double() :
                return False
            else :
                if self.get_format_priority() >= other.get_format_priority() :
                    return True
                else :
                    return False
    def valid(self) -> bool :
        return self.first_lang.valid()
    #主字幕是否中文
    def is_main_ch(self) -> bool :
        return self.first_lang == SUB_LANG.CHINESE or self.first_lang == SUB_LANG.CHT
    #主字幕是否英文
    def is_main_eng(self) -> bool :
        return self.first_lang == SUB_LANG.ENGLISH
    #主字幕是否日韩
    def is_main_JK(self) -> bool :
        return self.first_lang == SUB_LANG.JAPANESE or self.first_lang == SUB_LANG.KOREAN
    #主字幕是否东亚语言
    def is_main_east_asia(self) -> bool :
        return self.is_main_ch() or self.is_main_JK()
    #次字幕是否中文（一般不合理）
    def is_second_ch(self) -> bool :
        return self.second_lang == SUB_LANG.CHINESE or self.second_lang == SUB_LANG.CHT
    #次字幕是否英文
    def is_second_eng(self) -> bool :
        return self.second_lang == SUB_LANG.ENGLISH
    def is_second_JK(self) -> bool :
        return self.second_lang == SUB_LANG.JAPANESE or self.second_lang == SUB_LANG.KOREAN
    def is_second_east_asia(self) -> bool :
        return self.is_second_ch() or self.is_second_JK()
    #是否单语字幕
    def is_single(self) -> bool :
        return self.first_lang.valid() and not self.second_lang.valid() 
    #是否双语字幕
    def is_double(self) -> bool :
        return self.first_lang.valid() and self.second_lang.valid()
    #双语字幕是否为混合模式
    def is_mixed(self) -> bool :
        return self.is_double() and self.mixed
    #双语字幕是否为上下（大块）分离模式
    def is_depart(self) -> bool :
        return self.is_double() and not self.mixed and not self.spiral
    #双语字幕是否为螺旋（缠绕）分离模式
    def is_spiral(self) -> bool :
        return self.is_double() and not self.mixed and self.spiral
    #生成同时间轴的事件合并模式
    def gen_merge_mode(self) -> SUB_MERGER_MODE :
        mode = SUB_MERGER_MODE.UNKNOWN
        if self.is_single() :       #单语字幕
            mode = SUB_MERGER_MODE.MAIN_TO_MAIN
        elif self.is_double() :     #双语字幕
            if self.is_mixed() :    #混合双语模式，一个事件内有双语
                mode = SUB_MERGER_MODE.BOTH
            else :      #分离双语模式，无论是分区分离还是螺旋分离都一样
                mode = SUB_MERGER_MODE.MAIN_TO_SECONDARY
        return mode

#取得视频文件的bigb参数设置
def get_bigb_config(video_file : str, param : str, default : str='') -> str:
    if not os.path.exists(video_file) :
        return default
    value = default
    dir_name = os.path.dirname(video_file)
    file_info = os.path.splitext(video_file)
    ini_file = file_info[0] + '.ini'
    if not os.path.isfile(ini_file) :
        ini_file = file_info[0] + '.bigb.ini'
        if not os.path.isfile(ini_file) :
            ini_file = os.path.join(dir_name, 'bigb.ini')       #次一级从目录下的全局配置文件中读取
            if not os.path.isfile(ini_file) :
                ini_file = ''
    if ini_file != '' :
        parser = configparser.ConfigParser()
        parser.read(ini_file, encoding='utf-8')
        if parser.has_section('main') and parser.has_option('main', param) :
            tmp = parser.get('main', param).strip()
            if tmp != '' :
                value = tmp
                print('bigb配置文件(%s)读取到参数(%s=%s)。' %(ini_file, param, value))

    if param.upper() == 'SUB_TIME_OFFSET' :         #字幕偏移
        #再检查一遍是否有'字幕偏移.txt'，有则优先
        offset_file = os.path.join(dir_name, '字幕偏移.txt')
        if os.path.exists(offset_file) and os.path.isfile(offset_file) :
            try :
                f = open(offset_file, mode='r')
                tmp = f.readline().strip()
                f.close()
                if tmp.isdecimal() : 
                    value = tmp
                    print('字幕偏移文件{}读取到字幕偏移=({})。'.format(offset_file, value))
            except Exception as e :
                print('字幕时间偏移信息读取失败，原因：%s。' %(str(e)))
    return value

ASS_EVENT_XYZ_ZERO = (0, 0, 0)

class build_controller :
    def __init__(self) -> None :
        self.offset = 0                         #字幕偏移，毫秒级
        self.FORCE_N_SPLIT = False              #双语混合模式强制采用\N分割双语
        self.IGNORE_XYZ = ASS_EVENT_XYZ_ZERO    #忽略的ass事件前九个逗号中的坐标，格式为x,y,z
        self.IGNORE_FLAGS = list()              #事件正文中cut的无用或异常数据，一般是pos(x,x,x)和move(x,x,x)
        self.LANG_MODE = SUB_EVENT_LANG_MODE()
        self.ENG_SENTENCE_LEGAL = False               #英文字幕是否需要标准化（耗时操作）
        return
    def read_config(self, video_file : str) :
        print('begin BC read_config...')
        value = get_bigb_config(video_file, 'SUB_TIME_OFFSET', '0')
        try :
            self.offset = int(value)
        except Exception as e :
            self.offset = 0
            print('字幕时间偏移信息读取失败。')
        print('时间轴偏移量={}'.format(self.offset))
        self.FORCE_N_SPLIT = get_bigb_config(video_file, 'FORCE_N_SPLIT', '0') == '1'
        XYZ = get_bigb_config(video_file, 'IGNORE_EVENT_XYZ').split(',')
        if len(XYZ) == 3 :
            try :
                self.IGNORE_XYZ = (int(XYZ[0]), int(XYZ[1]), int(XYZ[2]))
            except Exception as e :
                self.IGNORE_XYZ = ASS_EVENT_XYZ_ZERO

        self.IGNORE_FLAGS = get_bigb_config(video_file, 'IGNORE_FLAGS').split('.')
        value = get_bigb_config(video_file, 'MAIN_LANG')
        if value.isdecimal() and int(value) > 0 :
            self.LANG_MODE.first_lang = int(value)
            value = get_bigb_config(video_file, 'SECONDARY_LANG')
            if value.isdecimal() and int(value) > 0 :
                self.LANG_MODE.second_lang = int(value)
                self.LANG_MODE.mixed = get_bigb_config(video_file, 'DOUBLE_LANG_MIXED', '0') == '1'
                if not self.LANG_MODE.mixed :
                    self.LANG_MODE.spiral = get_bigb_config(video_file, 'DOUBLE_LANG_SPIRAL', '0') == '1'
        self.ENG_SENTENCE_LEGAL = get_bigb_config(video_file, 'ENG_SENTENCE_LEGAL', '0') == '1'
        print('end BC read_config.')
        return
    def get_offset(self) -> int :
        return self.offset
    def valid(self) -> bool :
        return self.LANG_MODE.valid()
    def print(self) :
        print('开始打印控制器信息...')
        print('---时间偏移值={}'.format(self.get_offset()))
        print('---强制N分割双语={}'.format(self.FORCE_N_SPLIT))
        print('---INGORE_XYZ={}'.format(self.IGNORE_XYZ))
        print('---IGNORE FLAGS={}'.format(self.IGNORE_FLAGS))
        print('---ENG_SENTENCE_LEGAL={}'.format(self.ENG_SENTENCE_LEGAL))
        if self.LANG_MODE.valid() :
            self.LANG_MODE.print()
        else :
            print('---控制器的LANG_MODE目前无效。')
        return

class font_size_calculator :
    DEFAULT_SIZE = 19
    ULTRA_WIDE_SCALE = 2.1
    def __init__(self, width = 0, height = 0) -> None:
        self.width = width      #视频文件的宽
        self.height = height    #视频文件的高
        return
    def valid(self) -> bool :
        return self.height > 0 and self.width > 0
    def get_scale(self) -> float :
        scale = float(0)
        if self.valid() :
            scale = float(self.width / self.height)
        return scale
    #是否超宽高比视频（字体需要放大。解决方法：如有resx/resy则丢弃。）示例：嫌疑人X的献身（日版）
    def is_ultra_wide(self) -> bool :
        return self.get_scale() > font_size_calculator.ULTRA_WIDE_SCALE
    def less_equal_480P(self) -> bool :
        return self.height <= 480
    def less_equal_720P(self) -> bool :
        return self.height <= 720
    def less_equal_1080P(self) -> bool :
        return self.height <= 1080
    def less_equal_4K(self) -> bool :
        return self.height <= 2160
    def great_than_4K(self) -> bool :
        return self.height > 2160
    @staticmethod
    def get_second_size(main : int) -> int :
        second = 0
        if main >= 20 :
            second = main - 4
        elif main >= 15 :
            second = main - 3
        else :
            second = main
        return second
    #根据视频的分辨率和宽高比生成字幕字体大小
    def gen_font_size(self) -> int :
        main = font_size_calculator.DEFAULT_SIZE
        if self.valid() :
            scale = self.get_scale()
            assert(scale > 0)
            main = round(4.5 * scale + 10)
            '''
            if self.less_equal_480P() :
                main = round(8.15 * scale + 5.27)
                #main = round(6.93 * scale + 6.75)
            elif self.less_equal_720P() :
                main = round(4.90 * scale + 10.10)
                #main = round(2.93 * scale + 13.3)
            elif self.less_equal_1080P() :
                main = round(4.18 * scale + 10.37)
                #main = round(3.61 * scale + 11.82)
            else :      #4K及以上
                main = round(2.15 * scale + 13.95)
                #main = round(2.10 * scale + 14.11)
            '''
            if self.great_than_4K() :
                main = main - 1
        assert(main > 0)
        return main
    #根据ass字幕文件里的PlayResY生成字幕字体大小
    #对于有特效事件且原始字幕文件指定了PlayResX/PlayResY必须用这个函数生成
    #即新字幕文件要保留PlayResX/PlayResY适配特效事件
    #UltraWide，超宽比例视频，字体需要放大
    def gen_PlayRes_size(self, PlayResX : int , PlayResY : int) -> int :
        main = 0
        if PlayResY > 0 :
           #main = round((pow(PlayResY / 100, 2) * (-0.000204521) + (PlayResY / 100 * 0.0640793) + (-0.00855505)) * 100)
           #second = round((pow(PlayResY/100, 2) * (0.000792478) + (PlayResY / 100 * 0.0346447) + 0.0427191) * 100)
           main = round(0.058 * PlayResY + 3.57)
           #second = round(0.05 * PlayResY - 1.69)
           if self.is_ultra_wide() :
                main = int(round(main * 1.2))
                #second = int(round(second * 1.2))
        return main

#字幕输出设置
class output_config :
    #如字体为微软雅黑，则中间需要带一个space比较美观
    DEFAULT_SUB_NAME = '.bigc'
    DEFAULT_FONT_NAME = '微软雅黑'
    DEFAULT_CHS_NAME = '微软雅黑'
    DEFFAULT_ENG_NAME = 'arial'
    DEFAULT_MAIN_SIZE = 19          #17-19里选一个    
    DEFAULT_ALL_SIZE = 19
    SMALL_FONT_SIZE_ADJUST = 2      #小字体size偏移量
    #风格名称，字体名称，字体大小，字间距（0/1）
    ASS_MAIN_STYLE = 'Style: {},{},{},&H00FFFFFF,&HF0000000,&H00000000,&H32000000,0,0,0,0,100,100,{},0,1,1,1,2,5,5,1,1'
    ASS_SECONDARY_STYLE = 'Style: {},{},{},&H0062A8EB,&HF0000000,&H00000000,&H32000000,0,0,0,0,100,100,{},0,1,1,1,2,5,5,1,1'

    def __init__(self) -> None :
        self.name = output_config.DEFAULT_SUB_NAME
        self.main_font_name = output_config.DEFAULT_CHS_NAME
        self.main_font_size = output_config.DEFAULT_MAIN_SIZE
        self.second_font_name = output_config.DEFFAULT_ENG_NAME
        return
    def get_space(font_name : str) -> int :
        ONE_SPACES = ('雅黑', 'YAHEI', )
        for OS in ONE_SPACES :
            if font_name.upper().find(OS) >= 0 :
                return 1
        return 0
    def gen_ass_font_style(self, style : ASS_FONT_STYLE) -> str :
        line = ''
        if style == ASS_FONT_STYLE.DEFAULT :
            space = output_config.get_space(self.get_default_name())
            line = output_config.ASS_MAIN_STYLE.format(style.get_name(), self.get_default_name(), self.get_default_size(), space)
        elif style == ASS_FONT_STYLE.MAIN :
            space = output_config.get_space(self.get_main_name())
            line = output_config.ASS_MAIN_STYLE.format(style.get_name(), self.get_main_name(), self.get_main_size(), space)
        elif style == ASS_FONT_STYLE.SECOND :
            space = output_config.get_space(self.get_second_name())
            line = output_config.ASS_SECONDARY_STYLE.format(style.get_name(), self.get_second_name(), self.get_second_size(), space)
        else :
            assert(False)
        return line
    def get_style_name(self, MAIN=True) -> str :
        name = 'default'
        if MAIN :
            name = ASS_FONT_STYLE.MAIN.get_name()
        else :
            name = ASS_FONT_STYLE.SECOND.get_name()
        return name
    def is_middle_font(font_name : str) -> bool :
        MIDDLE_FONTS = ('字幕黑体M', )
        for mf in MIDDLE_FONTS :
            if font_name.upper() == mf :
                return True
        return False
    def set_main_info(self, BC : build_controller, name : str, size : int = 0) :
        if len(name) > 0 :
            self.main_font_name = name
        else :
            if BC.LANG_MODE.is_main_east_asia() :
                self.main_font_name = output_config.DEFAULT_CHS_NAME
            else :
                self.main_font_name = output_config.DEFFAULT_ENG_NAME
        if size > 0 :
            self.main_font_size = size
            if not output_config.is_middle_font(self.main_font_name) :
                self.main_font_size += output_config.SMALL_FONT_SIZE_ADJUST
        else :
            self.main_font_size = output_config.DEFAULT_MAIN_SIZE
        return
    def set_second_info(self, BC : build_controller, name : str) :
        if len(name) > 0 :
            self.second_font_name = name
        else :
            if BC.LANG_MODE.is_second_east_asia() :
                self.second_font_name = output_config.DEFAULT_CHS_NAME
            else :
                self.second_font_name = output_config.DEFFAULT_ENG_NAME
        return
    #取得主字体颜色
    def get_main_color(self) -> str :
        return '&H00FFFFFF'
    #取得次字体颜色
    def get_second_color(self) -> str :
        return '&H0062A8EB'
    def get_main_name(self) -> str :
        return self.main_font_name
    def get_main_size(self) -> int :
        return self.main_font_size
    def main_valid(self) -> bool :
        return len(self.get_main_name()) > 0
    def get_second_name(self) -> str :
        return self.second_font_name
    def get_second_size(self) -> int :
        if self.main_font_size > output_config.DEFAULT_MAIN_SIZE :
            return self.main_font_size - 4
        else :
            return self.main_font_size - 3
    def second_valid(self) -> bool :
        return len(self.get_second_name()) > 0
    def get_default_name(self) -> str :
        return output_config.DEFAULT_FONT_NAME
    def get_default_size(self) -> int :
        return output_config.DEFAULT_ALL_SIZE
    def default_valid(self) -> bool :
        return len(self.get_default_name()) > 0
    def get_desc(self) -> str :
        if len(self.name) == 0 :
            self.name = output_config.DEFAULT_SUB_NAME
        elif not self.name.startswith('.') :
            self.name = '.' + self.name
        return self.name
    
def test() :
    #b1 = datetime.strptime()
    b2 = datetime.min
    print(b2)
    b3 = datetime.min
    if b2 > b3 :
        print('great')
    elif b3 > b2 :
        print('less')
    elif b2 == b3 :
        print('equal')
    else :
        print('unknown')
    #e1 = datetime.strptime()
    
    return

#test()

