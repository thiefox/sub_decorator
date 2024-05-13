from __future__ import annotations

import re
from datetime import datetime

from com_utils import StrHandler
from subtitle.sub_event import sub_event

import subtitle.defs as defs

#srt事件的行区间信息
class event_interval(object) :
    INVALID = -1
    def __init__(self) -> None :
        self.eb = event_interval.INVALID        #事件开始的行号
        self.he = event_interval.INVALID        #头（索引+时间戳）结束的行号。不包括end，即实际的end为end-1
        self.ee = event_interval.INVALID        #事件结束的行号。不包括end，即实际的end为end-1
        return
    def get_event_begin(self) -> int :
        return self.eb
    def set_event_begin(self, begin : int) :
        self.eb = begin
    def begin_valid(self) -> bool :
        return self.get_event_begin() != event_interval.INVALID
    def get_header_end(self) -> int :
        return self.he
    def set_header_end(self, end : int) :
        self.he = end
    def get_event_end(self) -> int :
        return self.ee    
    def set_event_end(self, end : int) :
        self.ee = end
    #头区间有效（事件区间不一定有效）
    def header_interval_valid(self) -> bool :
        valid = self.begin_valid() and self.get_header_end() != event_interval.INVALID and self.get_header_end() > self.get_event_begin()
        return valid
    #事件区间有效（头区间一定有效）
    def event_interval_valid(self) -> bool :
        valid = self.begin_valid() and self.get_event_end() != event_interval.INVALID
        if valid :
            assert(self.header_interval_valid())
            pass
        return valid
    #取得头的行号区间
    def get_header_interval(self) -> int :
        interval = event_interval.INVALID
        if self.header_interval_valid() :
            interval = self.get_header_end() - self.get_event_begin()
        return interval
    #取得数据的行号区间
    def get_date_interval(self) -> int :
        interval = event_interval.INVALID
        if self.event_interval_valid() :
            interval = self.get_event_end() - self.get_header_end()
        return interval
    #取得整个事件的行号区间
    def get_event_interval(self) -> int :
        interval = event_interval.INVALID
        if self.event_interval_valid() :
            interval = self.get_event_end() - self.get_event_begin()
        return interval
   
class srt_sub_event(sub_event) :
    TIME_FORMATS = (r'(\d{1,2}:\d{1,2}:\d{1,2},\d{1,3})', r'(\d{1,2}:\d{1,2}:\d{1,2}:\d{1,3})', r'(\d{1,2}:\d{1,2}:\d{1,2}.\d{1,3})', )
    TIME_SPLITTER = '-->'
    def __init__(self) :
        super().__init__()
        self.index = -1             #SRT事件的索引号
        self._interval = event_interval()
        return
    @property
    def inter(self) :
        return self._interval
    def set_event_begin(self, pos : int) :
        self._interval.set_event_begin(pos)
    def set_header_end(self, pos : int) :
        self._interval.set_header_end(pos)
    def set_event_end(self, pos : int) :
        self._interval.set_event_end(pos)        
    def index_valid(self) -> bool :
        return self.index >= 0
    def print_interval(self) -> str :
        return '(i={})(eb={}, he={}, ee={})'.format(self.index, self.inter.eb, self.inter.he, self.inter.ee)
    def header_valid(self) -> bool :
        return self.inter.header_interval_valid()
    #重载函数
    def txt_valid(self) -> bool :
        return self.index_valid() and super().txt_valid()
    #重载函数
    def analysis(self) -> defs.SUB_EVENT_LANG_MODE :
        lm = defs.SUB_EVENT_LANG_MODE()
        if super().has_mt() :
            txt = StrHandler.rip_srt_sub_closed_str(super().get_mt())
            lm.first_lang = defs.SUB_LANG.check(txt)
        if super().has_st() :
            txt = StrHandler.rip_srt_sub_closed_str(super().get_st())
            lm.second_lang = defs.SUB_LANG.check(txt)
        if lm.first_lang.valid() and lm.second_lang.valid() :
            assert(lm.first_lang.get_int() != lm.second_lang.get_int())
            lm.is_mixed = True      #单事件内包含双语
        return lm

    def set_index(self, index : int) :
        self.index = index
        return
    def get_index(self) -> int :
        return self.index

    #由字符串生成时间戳数据
    def build_time(self, srt_time : str) -> bool :
        if super().time_valid() :   #已经有时间戳数据
            return False
        success = False
        bt, et = srt_sub_event._rip_time(srt_time)
        if bt != datetime.min and et != datetime.min :
            super().set_time_info(bt, et)
            success = True
        else :
            print('异常：解析时间信息失败2，data=%s.' %(srt_time))
            #assert(False)
        return success
    
    #从raw data生成main/secondary字幕文本
    def build_txt(self, DOUBLE=0, DEPART=0) -> bool :
        assert(not self.has_mt())
        for line in self.raw_lines :
            line = line.strip()
            if len(line) == 0 : #空行
                continue
            txts = StrHandler.rip_srt_sub_closed(line)
            #txts = srt_sub_event._rip_pure_txts(line)
            if len(txts) == 0 :
                continue
            if DOUBLE == 1 :    #单语字幕
                for txt in txts :
                    self.append_mt(txt)
            else :              #双语字幕或未知
                for txt in txts :
                    if not self.has_mt() :      #主字幕尚未有数据
                        self.append_mt(txt)
                    else :
                        if self.same_lang_as_main(txt) :
                            self.append_mt(txt)
                        else :
                            self.append_st(txt)
        return self.has_mt()
        
    #line：数据行
    #LAST：之前的最后一个index值
    #成功返回索引值，失败返回-1.
    def _rip_index(line : str, LAST = -1) -> int :
        index = -1 
        MAX_INDEX = 10000
        MAX_SKIP = 100
        if line.isdecimal() :
            i = int(line)
            if LAST >= 0 :      #指定了LAST值
                if i >= LAST - MAX_SKIP and i <= LAST + MAX_SKIP :
                    index = i
            else :
                index = i
        if index > MAX_INDEX :
            index = -1
        return index
    #由字符串生成时间戳数据
    def _rip_time(line : str) -> tuple :
        bt = et = datetime.min
        line = line.replace(' ', '')
        index = line.find(srt_sub_event.TIME_SPLITTER)      
        if index > 0 :      #找到时间分隔符
            str_begin = line[:index].strip()
            str_end = line[index+len(srt_sub_event.TIME_SPLITTER):].strip()
            #print('find splitter 1, left={}, right={}'.format(str_begin, str_end))
            for f in srt_sub_event.TIME_FORMATS :
                info = re.search(f, str_begin, re.I) 
                if info is not None :
                    str_begin = info.group()
                    bt = sub_event.time_info_2_datetime(str_begin)
                    break
            for f in srt_sub_event.TIME_FORMATS :
                info = re.search(f, str_end, re.I) 
                if info is not None :
                    str_end = info.group()
                    et = sub_event.time_info_2_datetime(str_end)
                    break
            #print('find splitter 2, left={}, right={}'.format(str_begin, str_end))
        begin_s = bt.strftime('%H:%M:%S.%f')[:-3]
        end_s = et.strftime('%H:%M:%S.%f')[:-3]
        #print('_rip_time finished, begin={}, end={}'.format(begin_s, end_s))
        return bt, et
    #尝试从pos开始找到一个事件头（索引行+时间戳行）
    @staticmethod
    def search_header(lines : list, pos : int, LAST_INDEX = -1) -> srt_sub_event :
        #print('begin search_header, pos={}, LI={}'.format(pos, LAST_INDEX))
        se = srt_sub_event()
        if pos < 0 or pos >= len(lines) :
            #print('pos failed, return')
            return se
        i = pos
        while i < len(lines) :
            line = lines[i].strip()
            #print('i={}, line={}'.format(i, line))
            #print('se info={}'.format(se.print_interval()))
            if line == '' :
                i += 1
                continue     
            if not se.inter.begin_valid() :
                se.index = srt_sub_event._rip_index(line, LAST_INDEX)
                if se.index_valid() :  #找到一行整数值，检查下一个有效行是否为时间戳
                    se.set_event_begin(i)
                i += 1
            else :
                se.begin_time, se.end_time = srt_sub_event._rip_time(line)
                #print('after rip time={}, i={}, time_info={}'.format(line, i, se.print_time_axis()))
                if not se.time_valid() :
                    se = srt_sub_event()
                    #print('time failed, continue...')
                    continue            #继续往下找, 这里i不+1，这行需要重新检测是否索引行
                else :  #索引行下跟着时间戳行, bingo
                    se.set_header_end(i+1)
                    break
        #print('end search_header, time_info={}, inter_info={}'.format(se.print_time_axis(), se.print_interval()))
        return se
    #尝试找到一个完整的事件
    @staticmethod
    def search_event(lines : list, pos : int, LAST_INDEX = -1) -> srt_sub_event :
        #print('begin search_event, lc={}, pos={}, LI={}...'.format(len(lines), pos, LAST_INDEX))
        first_e = srt_sub_event.search_header(lines, pos, LAST_INDEX)
        if first_e.header_valid() :    #找到有效事件头（索引+时间）
            assert(first_e.inter.get_event_begin() >= pos)
            if LAST_INDEX >= 0 :
                LAST_INDEX += 1
            next_e = srt_sub_event.search_header(lines, first_e.inter.get_header_end(), LAST_INDEX)
            if next_e.header_valid() :
                assert(next_e.inter.get_event_begin() > first_e.inter.get_event_begin())
                first_e.set_raw(lines[first_e.inter.get_header_end():next_e.inter.get_event_begin()])
                first_e.set_event_end(next_e.inter.get_event_begin())
            else :  #无法找到下一个有效事件（索引+时间戳）
                #print('查找下一个事件头失败，last event。')
                first_e.set_raw(lines[first_e.inter.get_header_end():len(lines)])    #当前事件即为最后一个事件
                first_e.set_event_end(len(lines))
        else :      #无法找到有效事件
            #print('查找srt事件头失败。')
            pass
        #print('end search_event, time_info={}, inter_info={}'.format(first_e.print_time_axis(), first_e.print_interval()))
        return first_e
