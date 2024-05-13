import os
import copy
import datetime

from com_utils import StrHandler
from com_utils import FileOpWrapper
from com_utils import config

import subtitle.defs as defs
from subtitle.sub_filer import sub_filer
from subtitle.ass_sub_event import ass_sub_event

class ass_sub_filer(sub_filer) :
    ASS_SESSION_SCRIPT = '[Script Info]'
    ASS_SCRIPT_PLAYX = 'PlayResX:'
    ASS_SCRIPT_PLAYY = 'PlayResY:'

    ASS_SESSION_V4STYLE = '[V4+ Styles]'
    ASS_SESSION_V4STYLE_OLD = '[V4 Styles]'
    ASS_SESSION_EVENTS = '[Events]'

    ASS_V4STYLE_HEADER = 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding'
    FONT_NAME_MSYH = '微软雅黑'
    FONT_NAME_ZMHT = '字幕黑体M'
    FONT_NAME_ARIAL = 'arial'
    FONT_NAME_OPTIMA = 'Optima'

    #字体风格名称
    ASS_BIGB_DEFAULT_NAME = 'default'
    ASS_BIGB_MAIN_NAME = 'BIGBM'
    ASS_BIGB_SECONDARY_NAME = 'BIGBS'

    #默认字体（风格名称，字体，大小）->default, 微软雅黑, 20
    #ASS_BIGB_DEFAULT_STYLE = 'Style: {},{},{},&H00FFFFFF,&HF0000000,&H00000000,&H32000000,0,0,0,0,100,100,1,0,1,1,1,2,5,5,1,1'
    ASS_BIGB_DEFAULT_STYLE = 'Style: {},{},{},&H00FFFFFF,&HF0000000,&H00000000,&H32000000,0,0,0,0,100,100,0,0,1,1,1,2,5,5,1,1'
    #兼容性好的式样版本(微软雅黑和arial)
    #spacing从1改成0
    ASS_BIGB_MAIN_STYLE = 'Style: {},{},{},&H00FFFFFF,&HF0000000,&H00000000,&H32000000,0,0,0,0,100,100,0,0,1,1,1,2,5,5,1,1'
    ASS_BIGB_SECONDARY_STYLE = 'Style: {},{},{},&H0062A8EB,&HF0000000,&H00000000,&H32000000,0,0,0,0,100,100,0,0,1,1,1,2,5,5,1,1'
    #视觉效果好的式样版本，默认版本17/14（字幕黑体M和Optima）
    ASS_BIGB_MAIN_STYLE_EX = 'Style: {},{},{},&H00FFFFFF,&HF0000000,&H00000000,&H32000000,0,0,0,0,100,100,0,0,1,1,1,2,5,5,1,1'
    ASS_BIGB_SECONDARY_STYLE_EX = 'Style: {},{},{},&H0062A8EB,&HF0000000,&H00000000,&H32000000,0,0,0,0,100,100,0,0,1,1,1,2,5,5,1,1'
    #ASS_BIGB_MAIN_DEFAULT_SIZE = 17
    #ASS_BIGB_SECONDARY_DEFAULT_SIZE = 14

    ASS_EVENT_HEADER = 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text'
    ASS_EVENT_OLD_HEADER = 'Format: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text'

    def __init__(self) :
        super().__init__()
        self.play_res_x = 0
        self.play_res_y = 0
        self.has_effect = False      #是否有特效事件
        self.raw_header = ''
        self.scripts = list()
        self.styles = list()
        return
    def copy_from(self, other : sub_filer) :
        self.file_name = other.file_name
        self.video_file = other.video_file
        #self.lines = list(other.lines)
        #self.format = other.format
        self.events = list()
        for event in other.events :
            ae = ass_sub_event()
            ae.copy_from(event)
            self.events.append(ae)
        #self.events = list(other.events)       #复制一份事件
        self.BC = copy.deepcopy(other.BC)
        return 
    def cut_ignore_flags(self, input : str, INSENSITIVE=True) -> str :
        output = input
        for FLAG in self.BC.IGNORE_FLAGS :
            FLAG = FLAG.strip()
            if INSENSITIVE :
                pos = output.lower().find(FLAG.lower())
                if pos >= 0 :
                    output = output[:pos] + output[pos+len(FLAG):]
            else :
                output = output.replace(FLAG, '')
        return output
    def is_BIGB_style(style : str) -> bool :
        BIGBSTYLE = 'style:bigb'
        format = style.replace(' ', '').lower()
        return format.startswith(BIGBSTYLE)
    def header_valid(self) -> bool :
        valid = len(self.scripts) > 0 and len(self.styles) > 0
        return valid
    def build_header(self) -> bool :
        self.scripts = list()
        self.play_res_x = self.play_res_y = 0        
        self.styles = list()
        self.scripts = StrHandler.read_session(ass_sub_filer.ASS_SESSION_SCRIPT, self.lines)
        for script in self.scripts :
            tmp = script.replace(' ', '').lower()
            i = tmp.find(ass_sub_filer.ASS_SCRIPT_PLAYX.lower())
            if i == 0 :
                x = tmp[len(ass_sub_filer.ASS_SCRIPT_PLAYX):]
                if x.isdecimal() :
                    self.play_res_x = int(x)
            else :
                i = tmp.find(ass_sub_filer.ASS_SCRIPT_PLAYY.lower())
                if i == 0 :
                    y = tmp[len(ass_sub_filer.ASS_SCRIPT_PLAYY):]
                    if y.isdecimal() :
                        self.play_res_y = int(y)

        print('通知：萃取到res_x=(%d)和res_y=(%d).' %(self.play_res_x, self.play_res_y))

        #print('script段读到(%d)行数据。' %len(script_data))
        styles = StrHandler.read_session(ass_sub_filer.ASS_SESSION_V4STYLE, self.lines)
        if len(styles) == 0 :
            styles = StrHandler.read_session(ass_sub_filer.ASS_SESSION_V4STYLE_OLD, self.lines)
        #print('style段读到(%d)行数据。' %len(style_data))
            
        index = -1
        if len(styles) > 0 :
            format_line = str(styles[0])
            format_line = StrHandler.strip_all(format_line)
            format_line = StrHandler.str_escape(format_line)
            standard = ass_sub_filer.ASS_V4STYLE_HEADER.replace(' ', '')
            if format_line.lower() == standard.lower() :
                index = 1
            else :
                if format_line.lower().startswith('style:') :
                    index = 0
                else :
                    #异常的style数据
                    pass
        if index >= 0 :
            for style in styles[index:] :
                if not ass_sub_filer.is_BIGB_style(style) :
                    self.styles.append(style)
        return self.header_valid()
    #检测有效事件的第一行索引
    def get_event_index(line : str) -> int :
        index = -1
        line = StrHandler.strip_all(line)
        line = StrHandler.str_escape(line).lower()
        STANDARD_NEW = ass_sub_filer.ASS_EVENT_HEADER.replace(' ', '')
        STANDARD_OLD = ass_sub_filer.ASS_EVENT_OLD_HEADER.replace(' ', '')
        if line == STANDARD_NEW.lower() or line == STANDARD_OLD.lower() :
            index = 1
        elif line.startswith('format:') :         #各种诡异的写法，比如用空格分隔
            index = 1
        elif line.startswith(ass_sub_event.ASS_EVENT_BEGIN.strip()) :       #直接开始数据行
            index = 0
        else :      #异常
            pass
        return index

    def build_events(self) -> bool :
        self.events = list()
        datas = StrHandler.read_session(ass_sub_filer.ASS_SESSION_EVENTS, self.lines)
        if len(datas) == 0 :
            return
        index = ass_sub_filer.get_event_index(datas[0])
        if index < 0 :
            return False

        for line in datas[index:] :
            line = StrHandler.strip_RN(line)
            line = self.cut_ignore_flags(line)
            event = ass_sub_event.build_event(line, self.BC)
            if event is None :
                continue
            if event.is_effect() :
                self.has_effect = True
            self.events.append(event)    #延缓合并
        return len(self.events) > 0
    #重载函数
    def build(self) -> bool :
        if self.build_header() :
            if self.build_events() :
                return True
        return False
    #复制事件集
    def copy_events(self, other : sub_filer) -> bool :
        success = False
        if len(self.events) == 0 and len(other.get_events()) > 0 :
            self.events = list(other.get_events())       #复制一份事件
            success = True
        return success
    #根据PlayResX和PlayResY生成字幕字体大小
    #ASS的PlayResXY字体大小优先于视频尺寸字体大小
    #tuple[0]为主字幕大小，tuple[1]为次字幕大小
    def gen_font_size(self) -> tuple :
        main_size = None
        fs_calc = defs.font_size_calculator()
        if os.path.isfile(self.video_file) :
            vi = FileOpWrapper.get_video_file_info(self.video_file)
            if vi is not None :
                fs_calc = defs.font_size_calculator(vi.width, vi.height)
            
        if self._need_PlayResXY() :
            main_size = fs_calc.gen_PlayRes_size(self.play_res_x, self.play_res_y)
        else :
            main_size = fs_calc.gen_font_size()
        return main_size, defs.font_size_calculator.get_second_size(main_size)

    #是否需要保留PlayResX/PlayResY信息
    def _need_PlayResXY(self) -> bool :
        return self.play_res_x > 0 and self.play_res_y > 0 and self.has_effect

    #生成默认的script段
    def _gen_default_scripts(self) -> list :
        lines = list()
        line = ass_sub_filer.ASS_SESSION_SCRIPT
        lines.append(line)
        if self.file_name != '' :
            basename = os.path.basename(self.file_name)
            basename = os.path.splitext(basename)[0]
            line = 'Title : ' + basename
            lines.append(line)
        FIXED_LINES = { 'Script Updated By: BIGB', 'Synch Point: 1', 'ScriptType: v4.00+', 'Collisions: Normal', 'WrapStyle: 0', 'Timer: 100.0000' }
        for fl in FIXED_LINES :
            lines.append(fl)
        return lines
    #输出script段
    def output_script_session(self) -> list :
        REPLACE_LINES = ( ('wrapstyle', 'WrapStyle: 0'), ('scripttype', 'ScriptType: v4.00+'), ('playdepth', ''), ('scaledborderandshadow', ''), )
        lines = list()
        if len(self.scripts) == 0:
            lines = self._gen_default_scripts()
        else :
            lines.append(ass_sub_filer.ASS_SESSION_SCRIPT)
            for line in self.scripts :
                line = str(line)
                if line.lower().find('playresx') >= 0 or line.lower().find('playresy') >= 0 :
                    if not self._need_PlayResXY() :
                        line = ''
                else :
                    for RL in REPLACE_LINES :
                        if line.lower().find(RL[0]) >= 0 :
                            line = RL[1]
                            break

                if len(line) > 0 :
                    lines.append(line)
        lines.append('')
        return lines
    def _gen_font_style(style : defs.ASS_FONT_STYLE, config : defs.output_config) -> str :
        line = ''
        if style == defs.ASS_FONT_STYLE.DEFAULT :
            line = ass_sub_filer.ASS_BIGB_DEFAULT_STYLE.format(style.get_name(), config.get_default_name(), config.get_default_size())
        return line

    #生成默认的style段
    def _gen_default_styles(self, config : defs.output_config) -> list:
        lines = list()
        lines.append(ass_sub_filer.ASS_SESSION_V4STYLE)
        lines.append(ass_sub_filer.ASS_V4STYLE_HEADER)
        #默认字体
        if config.default_valid() :
            lines.append(config.gen_ass_font_style(defs.ASS_FONT_STYLE.DEFAULT))
            #lines.append(ass_sub_filer.ASS_BIGB_DEFAULT_STYLE.format(config.get_default_name(), config.get_default_size()))
        #主字幕字体
        assert(config.main_valid())
        if config.main_valid() :
            lines.append(config.gen_ass_font_style(defs.ASS_FONT_STYLE.MAIN))
            #lines.append(ass_sub_filer.ASS_BIGB_MAIN_STYLE.format(config.get_main_name(), config.get_main_size()))
        #次字幕字体
        if self.BC.LANG_MODE.is_double() :
        #if config.second_valid() :
            lines.append(config.gen_ass_font_style(defs.ASS_FONT_STYLE.SECOND))
            #lines.append(ass_sub_filer.ASS_BIGB_SECONDARY_STYLE.format(config.get_second_name(), config.get_second_size()))
        return lines   
     
    def output_style_session(self, config : defs.output_config) -> list :
        assert(config is not None)
        lines = self._gen_default_styles(config)

        for line in self.styles :           #保留源ass里的其它styles
            data = line.lower().replace(' ', '')
            if data.find('style:default,') >= 0 :
                continue
            lines.append(line)
        lines.append('')
        return lines

    #输出事件头
    def output_event_header(self) -> list :
        lines = list()
        lines.append(ass_sub_filer.ASS_SESSION_EVENTS)
        lines.append(ass_sub_filer.ASS_EVENT_HEADER)
        return lines
    #生成bigb系列字幕文件名
    def gen_bigb_name(self, BEST=False) -> str :
        assert(len(self.video_file) > 0)
        assert(os.path.exists(self.video_file))
        sub_name = ''
        header = os.path.splitext(self.video_file)[0]
        if BEST :
            sub_name = header + '.bigb.ass'
        else :
            sub_name = header + '.bigbc.ass'
        return sub_name
    #生成输出的配置
    def get_output_config(self, BEST=False) -> defs.output_config :
        print('开始生成output_config, BEST={}'.format(BEST))
        font_size = self.gen_font_size()
        if font_size[0] <= 0 :
            print('异常：无法生成合适的字体大小。')
            return None
        self.BC.print()
        print('生成字体大小，main={}, second={}'.format(font_size[0], font_size[1]))
        global_config = config.bigma_config()
        BEST_CHS_FONT = global_config.get_subtitle_best_chs_font()
        BEST_ENG_FONT = global_config.get_subtitle_best_eng_font()

        op_config = defs.output_config()
        if BEST :
            if self.BC.LANG_MODE.is_main_east_asia() :
                print('主字幕为东亚语言...')
                op_config.set_main_info(self.BC, BEST_CHS_FONT, font_size[0])
            else :
                print('主字幕为英语系语言...')
                op_config.set_main_info(self.BC, BEST_ENG_FONT, font_size[0])
        else :
            print('兼容性优先，由内部设定字体...')
            op_config.set_main_info(self.BC, '', font_size[0])

        if self.BC.LANG_MODE.is_double() :
            if BEST :
                if self.BC.LANG_MODE.is_second_east_asia() :
                    op_config.set_second_info(self.BC, BEST_CHS_FONT)
                else :
                    op_config.set_second_info(self.BC, BEST_ENG_FONT)
            else :
                op_config.set_second_info(self.BC, '')
        print('字幕主字体={}, size={}'.format(op_config.get_main_name(), op_config.get_main_size()))
        assert(op_config.get_main_name() != '' and op_config.get_main_size() > 0)
        if self.BC.LANG_MODE.is_double() :
            print('字幕次字体={}, size={}'.format(op_config.get_second_name(), op_config.get_second_size()))
            assert(op_config.get_second_name() != '' and op_config.get_second_size() > 0)
            pass
        return op_config  

    #生成bigb字幕文件
    def _save_bigb(self, file_name : str, config : defs.output_config) -> bool :
        s_time = datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3]
        print('time={}, begin _save_bigb, file_name={}...'.format(s_time, file_name))        
        if not self.BC.valid() :
            print('异常：BC控制器异常，无法生成字幕。')
            return False
        self.BC.print()
        if self.BC.get_offset() != 0 :
            print('重要：字幕时间偏移={}毫秒.'.format(self.BC.get_offset()))

        lines = list()
        lines.extend(self.output_script_session())
        lines.extend(self.output_style_session(config))
        lines.extend(self.output_event_header())
        print('event count={}'.format(len(self.events)))
        index = 0
        for event in self.events :
            #print('time={}, index={}'.format(datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3], index))
            assert(isinstance(event, ass_sub_event))
            #event = ass_sub_event(event)
            line = event.output_event(config.get_style_name(True), config.get_style_name(False), self.BC)
            if len(line) > 0 :
                lines.append(line)
            else :
                print('异常：事件生成异常，raw={}.'.format(event.get_raw()))
            index += 1
        print('共生成({})行数据。'.format(len(lines)))
        for i in range(len(lines)) :
            lines[i] = sub_filer.confirm_new_line_flag(lines[i])
        f = open(file_name, mode='w', encoding='utf-8')
        f.writelines(lines)
        f.close()
        s_time = datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3]
        print('end _save_bigb, time={}.'.format(s_time))
        return True

    #重载此函数
    def save_bigb(self) -> bool :
        success = False
        is_best = True
        print('开始生成效果最好的字幕文件...')
        best_sub = self.gen_bigb_name(BEST=is_best)
        oc = self.get_output_config(BEST=is_best)
        if oc is not None :
            success = self._save_bigb(best_sub, oc)
        is_best = False
        print('开始生成兼容性最好的字幕文件...')
        compatible_sub = self.gen_bigb_name(BEST=is_best)
        oc = self.get_output_config(BEST=is_best)
        if oc is not None :
            success = self._save_bigb(compatible_sub, oc)
        return success


