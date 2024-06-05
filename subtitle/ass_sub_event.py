from __future__ import annotations

import re

from com_utils import StrHandler
from datetime import datetime, timedelta

import subtitle.defs as defs
from subtitle.sub_event import sub_event

class ass_sub_event(sub_event) :
    ASS_EVENT_BEGIN = 'dialogue: '
    SPLITTER = ','
    SPLITTER_COUNT = 9          #出现9个英文逗号后，为ASS字幕正文
    TEXT_LANG_SPLITTER =  '\\N'
    
    def __init__(self) :
        super().__init__()
        self.effect = False     #是否ass特效字幕，如ass_effect=True, 则整行数据保存在raw_data。时间数据仍需萃取，用于写入排序。
        #self.IgnoreXYZ = None       #None或者三元组tuple
        self.XYZ = tuple()
        return
    def _get_line(self) -> str :
        line = ''
        if len(self.raw_lines) == 1 :
            line = self.raw_lines[0]
        return line
    def copy_from(self, other : sub_event) :
        self.effect = False
        self.XYZ = tuple()
        self.raw_lines = other.raw_lines
        self.begin_time = other.begin_time
        self.end_time = other.end_time
        self.main_txt = other.main_txt
        self.secondary_txt = other.secondary_txt
        return
    #重载函数
    #是否特效事件
    def is_effect(self) -> bool :
        return self.effect
    #重载函数
    def txt_valid(self) -> bool :
        if self.is_effect() :
            return True
        else :
            return super().txt_valid()
    #重载函数
    def analysis(self) -> defs.SUB_EVENT_LANG_MODE :
        lm = defs.SUB_EVENT_LANG_MODE()
        if super().has_mt() :
            txt = StrHandler.rip_ass_sub_closed_str(super().get_mt())
            lm.first_lang = defs.SUB_LANG.check(txt)
        if super().has_st() :
            txt = StrHandler.rip_ass_sub_closed_str(super().get_st())
            lm.second_lang = defs.SUB_LANG.check(txt)
        if lm.first_lang.valid() and lm.second_lang.valid() :
            #print('first_lang={}, second_lang={}.'.format(lm.first_lang.get_int(), lm.second_lang.get_int()))
            #assert(lm.first_lang.get_int() != lm.second_lang.get_int())
            lm.mixed = True             #单事件内包含双语
        return lm        
    def is_txt_event(self) -> bool :
        return not self.is_effect()
    #由XYZ轴信息检测line是否为特效事件
    def is_effect_by_XYZ(line : str, IGNORE_XYZ : tuple) -> bool :
        ZERO_XYZ = (0, 0, 0)
        coordinate = ass_sub_event.get_XYZ(line)
        return coordinate != ZERO_XYZ and coordinate != IGNORE_XYZ
    #是否要做成重载函数？
    #ass_time_format = '0:02:38.60'. #ASS的毫秒要*10。即ass的最小时间单位为10毫秒。
    def format_datetime(time_info : datetime) -> str :
        return time_info.strftime('%H:%M:%S.%f')[1:-4]
    
    #是否要做成重载函数？srt_event也有这个函数
    def build_time(self, ass_line : str) -> bool:
        success = False
        if super().time_valid() :
            return False
        str_begin = str_end = ''
        index = ass_line.find(',')
        if index > 0 :
            bp = index + 1   #begin pos
            index = ass_line.find(',', index + 1)
            if index > 0 :
                str_begin = ass_line[bp:index]
                ep = index + 1    #end pos
                index = ass_line.find(',', index + 1)
                if index > 0 :
                    str_end = ass_line[ep:index]
        #print('ass time begin=%s, time end=%s.' %(str_begin, str_end))
        begin_info = sub_event.time_info_2_datetime(str_begin)
        end_info = sub_event.time_info_2_datetime(str_end)
        if begin_info is not None and end_info is not None :
            self.begin_time = begin_info
            self.end_time = end_info
            #print('ASS萃取的开始时间=%s, 结束时间=%s.' %(sub_event.datetime_2_srt(begin_info), sub_event.datetime_2_srt(end_info)))
            #print('100毫秒delta=%d.' %(self._get_time_delta(1)[1] ))
            success = True
        return success

    #取得事件头部的坐标信息
    def get_XYZ(line : str) -> tuple :
        X_INDEX = 5
        pos = (0, 0, 0)
        items = line.split(ass_sub_event.SPLITTER, ass_sub_event.SPLITTER_COUNT)
        if len(items) >= ass_sub_event.SPLITTER_COUNT :
            x = items[X_INDEX]
            y = items[X_INDEX + 1]
            z = items[X_INDEX + 2]
            if x.isdecimal() and y.isdecimal() and z.isdecimal() :
                pos = (int(x), int(y), int(z))
        return pos        
    def _get_XYZ(self) -> tuple :
        return ass_sub_event.get_XYZ(self._get_line())
    def output_XYZ_data(self) -> str:
        data = ''
        info = self._get_XYZ()
        if info is not None :
            data = '{:0>4d},{:0>4d},{:0>4d}'.format(info[0], info[1], info[2]) 
        else :
            data = '0000,0000,0000'
        return data
    #取得一个事件的正文部分（刨除头部九个逗号后的数据）
    def get_text(line : str) -> str :
        text = ''
        items = line.split(ass_sub_event.SPLITTER, ass_sub_event.SPLITTER_COUNT)
        if len(items) == ass_sub_event.SPLITTER_COUNT + 1 :
            text = items[ass_sub_event.SPLITTER_COUNT]
        return text        
    def _get_text(self) -> str:
        return ass_sub_event.get_text(self._get_line())
    #检测一段字符串是否是ass水印
    def is_watermark(str) -> bool :
        result = False
        if len(str) >= 500 and (StrHandler.get_number_count(str) >= 250) :
            result = True
        return result
    
    def output_event(self, main_style : str, secondary_style : str, bc : defs.build_controller) -> str :
        #begin, end, main_style, XYZinfo, main_text
        ASS_EVENT_SINGLE_FORMAT = 'Dialogue: 0,{},{},{},,{},,{}'
        #begin, end, main_style, XYZinfo, main_text, second_style, second_text
        ASS_EVENT_DOUBLE_FORMAT = 'Dialogue: 0,{},{},{},,{},,{}\\N{{\\r{}}}{}'
        assert(self.begin_time is not None and self.end_time is not None)
        if bc.get_offset() == 0 :
            str_begin = ass_sub_event.format_datetime(self.begin_time)
            str_end = ass_sub_event.format_datetime(self.end_time)
        else :
            str_begin = ass_sub_event.format_datetime(self.begin_time + timedelta(milliseconds=bc.get_offset()))
            str_end = ass_sub_event.format_datetime(self.end_time + timedelta(milliseconds=bc.get_offset()))
        line = ''
        XYZ_info = self.output_XYZ_data()
        #print('事件输出，特效={}, rc={}, raw={}'.format(self.is_effect(), len(self.get_raw()), self.get_raw()))
        if self.is_effect() :       #特效字幕
            line = ASS_EVENT_SINGLE_FORMAT.format(str_begin, str_end, main_style, XYZ_info, self._get_text())
        else :
            main = super().get_mt()
            second = super().get_st()
            if bc.ENG_SENTENCE_LEGAL :
                if bc.LANG_MODE.is_main_eng() :
                    main = StrHandler.eng_paragraph_adjust(main)
                elif bc.LANG_MODE.is_second_eng() :
                    second = StrHandler.eng_paragraph_adjust(second)
            if bc.LANG_MODE.is_single() :
                if len(main) > 0 :
                    line = ASS_EVENT_SINGLE_FORMAT.format(str_begin, str_end, main_style, XYZ_info, main)
            elif bc.LANG_MODE.is_double() :
                if len(main) > 0 or len(second) > 0 :
                    line = ASS_EVENT_DOUBLE_FORMAT.format(str_begin, str_end, main_style, XYZ_info, main, secondary_style, second)
            else :
                print('异常：输出时发现数据异常。main和second都没有数据。')
                self.print()
                assert(False)
        return line
    #检测某个事件是否为特效事件
    def is_effect_event(line : str, IGNORE_XYZ : tuple) -> bool :
        EFFECT_FLAGS = ('pos(', 'move(', )
        ALIGNMENT_FLAGS = (r'(\\an\d{1})', r'(\\a\d{1})', )        
        if ass_sub_event.is_effect_by_XYZ(line, IGNORE_XYZ) :
            return True
        #to do : 以后的检查是否要把line变成9个逗号后的正文？
        for ef in EFFECT_FLAGS :
            if line.lower().find(ef) >= 0 :
                return True
        for af in ALIGNMENT_FLAGS :
            info = re.search(af, line, re.I) 
            if info is not None :
                return True
        return False
    #侦测模式生成main/secondary
    #text：去除9个逗号后的事件pure text
    def build_txt_with_detect(self, text : str) :
        #pos = -1
        #second_part = False
        last_lang = -1
        parts = text.split(ass_sub_event.TEXT_LANG_SPLITTER)
        for raw in parts :
            if raw.strip() == '' :
                continue
            pure = StrHandler.rip_ass_sub_closed_str(raw)       #删除控制字符闭包数据？
            assert(isinstance(pure, str))
            if len(pure) == 0 :
                continue
            cur_lang = StrHandler.is_zh_or_eng(pure)
            if not self.has_mt() :
                self.set_mt(pure)
                last_lang = cur_lang
            elif not self.has_st() and cur_lang == last_lang :
                self.append_mt(pure)
            else :
                self.append_st(pure)
                last_lang = cur_lang
        return
    #由单行ass事件数据字符串生成event对象
    #Double=0未知，=1单语，=2双语。
    #老的函数名：rip_ass_line_ex
    def build_event(line : str, bc : defs.build_controller) -> ass_sub_event :
        #print('处理行数据={}'.format(line))
        event = ass_sub_event()
        event.set_raw([line])
        #event.raw_lines.append(line)

        if not event.build_time(line) :
            return None
        assert(event.time_valid())
        text = ass_sub_event.get_text(line)
        if text == '' or ass_sub_event.is_watermark(text) :   #水印数据
            return None
        
        if ass_sub_event.is_effect_event(line, bc.IGNORE_XYZ) :
            event.effect = True      #特效事件

        if bc.LANG_MODE.is_single() :   #单语字幕
            pure = StrHandler.rip_ass_sub_closed_str(text)
            event.set_mt(pure)
        elif bc.LANG_MODE.is_double() and not bc.LANG_MODE.is_mixed() :
            #分离模式双语字幕，一个事件内单语
            pure = StrHandler.rip_ass_sub_closed_str(text)
            event.set_mt(pure)
        elif bc.FORCE_N_SPLIT :
            parts = text.split(ass_sub_event.TEXT_LANG_SPLITTER, 1)
            if len(parts) == 2 :
                pure = StrHandler.rip_ass_sub_closed_str(parts[0])
                event.set_mt(pure)
                pure = StrHandler.rip_ass_sub_closed_str(parts[1])
                event.set_st(pure)
            else :
                pure = StrHandler.rip_ass_sub_closed_str(text)
                event.set_mt(pure)
        else :
            event.build_txt_with_detect(text)
        return event
