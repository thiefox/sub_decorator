from __future__ import annotations

import os
import copy
import chardet

import subtitle.defs as defs
from subtitle.sub_event import sub_event

class sub_filer(object) :
    def __init__(self) -> None:
        self.file_name = ''                                 #字幕文件的名字        
        self.video_file = ''
        self.lines = list()                                 #字幕文件原始数据，行数据集
        self.format = defs.SUB_FORMAT.UNKNOWN               #字幕格式
        #self.events = list()                                #事件列表
        self.events : list[sub_event] = []
        self.BC = defs.build_controller()                   #控制器
        return
    def get_events(self) -> list :
        return self.events
    def _init_build_controller(self) :
        print('begin _init BC...')
        if os.path.exists(self.video_file) :
            self.BC.read_config(self.video_file)
        elif os.path.exists(self.file_name) :
            self.BC.read_config(self.file_name)
        else :
            assert(False)
        self.BC.print()
        print('end _init_BC.')
        return
    #取得字幕文件的后缀，带'.'
    def get_suffix(self) -> str :
        suffix = ''
        if len(self.file_name) > 0 :
            suffix = os.path.splitext(self.file_name)[1]
        return suffix

    def attach_video(self, video_name : str) :
        self.video_file = video_name
        return
    #派生类重载此函数
    def build(self) -> bool :
        return False
    #派生类重载此函数
    def save_bigb(self) -> bool :
        return False
    #字幕加载函数
    #在加载过程的结尾会完成（双语）同时间轴事件的合并
    def load(self, file_name : str) -> bool :
        if self._load_lines(file_name) :
            self._init_build_controller()
            if self.build() :           #由派生类完成
                self.inner_merge()      #同时间轴事件合并处理
                self.analysis()         #字幕分析 to do 检查加在这里对不对
                return True
        return False
         
    #读入字幕文件的所有数据行到self.lines
    def _load_lines(self, file_name : str) -> bool :
        if not os.path.exists(file_name) or not os.path.isfile(file_name) :
            print('异常：字幕文件(%s)不存在。' %file_name)
            return False
        suffix = os.path.splitext(file_name)[1].lower()
        if suffix not in defs.SUB_FILE_TYPE :
            print('异常：文件(%s)非支持的字幕文件(%s)。' %(file_name, suffix))
            return False
        if suffix not in defs.REBUILD_SUB_FILE_TYPE :
            print('异常：文件(%s)非支持REBUILD的字幕文件(%s)。' %(file_name, suffix))
            return False
        f = open(file_name, mode='rb')
        data = f.read() 
        f.close()
        result = chardet.detect(data)
        encoding = ''
        confidence = 0.0
        if 'encoding' in result :
            encoding = result['encoding']
        if 'confidence' in result :
            confidence = result['confidence']
        if encoding == '' or confidence < 0.9 :
            print('异常：无法识别字幕文件(%s)的编码(e=%s, c=%.2f)。尝试utf-8...' %(file_name, encoding, confidence))
            encoding = 'utf-8'

        self.file_name = file_name
        self.lines = list()
        exce = False
        #print('字幕文件(%s)的编码=(%s), per=%.2f%%.' %(file_name, encoding, confidence))
        try :
            f = open(file_name, mode='r', encoding=encoding)
            self.lines = f.readlines()
            f.close()
            #print('字幕文件(%s)共读入(%d)行文本。' %(file_name, len(lines)))
        except Exception as e :
            #print('异常：处理文件(%s)系统异常，原因: %s.' %(file_name, str(e)))
            exce = True
            self.lines = list()
            if encoding.lower() == 'gb2312' :
                exce = False
                try :
                    f = open(file_name, mode='r', encoding='gbk') 
                    self.lines = f.readlines()
                    f.close()
                    #print('字幕文件(%s)用GBK复检模式打开成功，共读入(%d)行文本。' %(file_name, len(lines)))
                except Exception as e :
                    exce = True
                    self.lines = list()
        if exce :           #文件打开异常
            try :
                self.lines = list()
                f = open(file_name, mode='rb')
                for line in f :
                    line = line.decode(encoding, errors='ignore').rstrip('\n')
                    self.lines.append(line)
                f.close()
                #print('用宽松模式重新打开字幕文件(%s)成功。' %(file_name))
            except Exception as e :
                print('异常：用宽松模式仍无法打开文件(%s)，原因: %s.' %(file_name, str(e)))
                self.lines = list()
        return len(self.lines) > 0

    #同轴事件合并
    def merge_time_axis(self, PRECISION : defs.TIME_PRECISION) :
        '''
        def _search(events : list, event : sub_event, PRECISION : defs.TIME_PRECISION) -> sub_event :
            found_event = None
            for e in events :
                if e.is_txt_event() and event.is_same_time(e, PRECISION) :
                    found_event = e
                    break
            return found_event
        '''
        print('开始尝试同轴合并，时间轴参数={}, 事件数={}...'.format(PRECISION, len(self.events)))
        new_events = list()
        for event in self.events :
            if event.is_txt_event() :
                found = event.is_exist(new_events, PRECISION)
                #found = _search(new_events, event, PRECISION)
                if found :
                    if found.is_single() and event.is_single() and found.is_main_diff(event) :
                        found.merge_from(event, defs.SUB_MERGER_MODE.MAIN_TO_SECONDARY)
                        pass
                    else :
                        new_events.append(event)
                else :
                    new_events.append(event)
            else :
                new_events.append(event)
        
        if len(new_events) < len(self.events) :
            print('发生了{}个事件的合并，替换老事件集...'.format(len(self.events)-len(new_events)))
            self.events = new_events
        else :
            print('尝试合并完成，未发生合并，忽略。')
        return
    def cht_to_chs(self) :
        for event in self.events :
            event.cht_2_chs()
        return
    #文件内事件合并处理（一般用于把两个事件的双语字幕合并为一个事件）
    def inner_merge(self) :
        self.merge_time_axis(defs.TIME_PRECISION.MILLSECOND_100)
        return
    #尝试把两个单语字幕文件合成为一个双语字幕文件
    #other合成到self，other不变动。
    #合并成功返回True。
    def outer_merge(self, other : sub_filer) -> bool :
        TIME_MATCH_RATE = 0.7
        merged = False
        if self.BC.LANG_MODE.is_double() :
            return False
        if other.BC.LANG_MODE.is_double() :
            return False
        if self.BC.LANG_MODE.first_lang == other.BC.LANG_MODE.first_lang :
            return False
        new_events = list(self.events)      #复制一份事件
        all = 0
        matchs = 0
        for oe in other.events :
            oe = type(sub_event)(oe)
            if oe.is_txt_event() :
                all += 1
                found = oe.is_exist(new_events, defs.TIME_PRECISION.EXACT)
                if found :
                    matchs += 1
                    #to do : 双语合并操作
                    assert(not found.is_double())
                    assert(not oe.is_double())
                    found.merge_from(oe, defs.SUB_MERGER_MODE.MAIN_TO_SECONDARY)
                    pass
                else :
                    new_events.append(oe)
            else :
                pass
        if all > 0 and matchs / all >= TIME_MATCH_RATE :
            self.events = new_events        #替换成合并后的双语事件集
            merged = True
            self.analysis()
        return merged

    #取得字幕偏移信息，毫秒为单位，可以正负偏移
    def get_offset_millseconds(self) -> int :
        offset = 0
        value = defs.get_bigb_config(self.file_name, 'SUB_TIME_OFFSET', '0')
        try :
            offset = int(value)
        except Exception as e :
            print('字幕时间偏移信息读取失败。')
        return offset
    #确保字符串以\n结尾
    def confirm_new_line_flag(line : str) -> str :
        NEW_LINE_FLAG = '\n'
        if not line.endswith(NEW_LINE_FLAG) :
            line = line + NEW_LINE_FLAG
        return line
    
    #字幕语言信息检测
    def analysis(self) :
        print('开始-sub filer::analysis(分析), 总事件数={}...'.format(len(self.events)))
        lm = defs.SUB_EVENT_LANG_MODE()
        lm.path_file = self.file_name
        DOUBLE_RATIO = 0.6
        event_count = 0
        double_count = 0
        lang_dict = dict()
        for event in self.events :
            #event = type(sub_event)(event)
            if event.is_effect() :
                continue
            event_count += 1
            time_val = event.get_time_interval_str()
            assert(len(time_val) > 0)
            e_lm = event.analysis()
            if e_lm not in lang_dict :
                lang_dict[e_lm] = 1
            else :
                lang_dict[e_lm] += 1

            assert(e_lm.valid())
            if e_lm.is_double() :       #单个事件内双语
                double_count += 1
                lm.copy_from_event(e_lm)
        sorted_langs = sorted(lang_dict.items(), key = lambda x:x[1], reverse = True)
        if event_count == 0 :
            self.BC.LANG_MODE = defs.SUB_EVENT_LANG_MODE()
            print('结束1-sub filer::analysis.')    
            return
        elif double_count / event_count >= DOUBLE_RATIO :   #单事件内双语字幕
            assert(len(sorted_langs) > 0)
            #self.BC.LANG_MODE = lm
            self.BC.LANG_MODE = sorted_langs[0][0]
            #self.BC.print()
            print('结束2-sub filer::analysis, 双语/总事件={}/{}.'.format(double_count, event_count))    
            return
        #之后则只按单事件内单语处理（只检测主语言）
        time_matchs = 0         #相同时间轴的事件数量
        time_spirals = 0        #相同时间轴且缠绕的事件数量
        event_index = 0
        time_dict = dict()     #key为时间戳，value为事件索引
        lang_dict = dict()      #key为语言，value为事件数量
        for event in self.events :
            event_index += 1
            if event.is_effect() :      #特效事件
                continue
            time_val = event.get_time_interval_str()
            assert(len(time_val) > 0)
            e_lm = event.analysis()
            if not e_lm.valid() :
                assert(False)
            if e_lm.first_lang not in lang_dict :
                lang_dict[e_lm.first_lang] = 1
            else :
                lang_dict[e_lm.first_lang] += 1

            if time_val not in time_dict :     #在事件词典中没有找到
                time_dict[time_val] = event_index
            else :                              #在事件词典中找到
                if time_dict[time_val] >= 0 :
                    time_matchs += 1
                    if abs(time_dict[time_val] - event_index) == 1 :
                        time_spirals += 1
                    time_dict[time_val] = -1        #处理过标志
                else :
                    assert(False)       #出现了大于2个事件同时间轴
                    pass
        SECOND_SUB_RATE = 0.3
        langs = sorted(lang_dict.items(), key=lambda x: x[1], reverse=True)
        assert(len(langs) > 0)
        lm.reset_inner()         #复位
        lm.first_lang = langs[0][0]
        if len(langs) > 1 :     #有第二字幕
            temp_lang = langs[1][0]
            second_count = langs[1][1]
            if temp_lang != lm.first_lang and second_count / event_count >= SECOND_SUB_RATE :
                lm.second_lang = temp_lang
        else :
            lm.set_no_second()
        
        lm.mixed = False
        SPIRAL_RATE = 0.7
        lm.is_double()
        if lm.second_lang != defs.SUB_LANG.UNKNOWN :       #有第二字幕
            lm.time_match_rate = time_matchs * 2 / event_count
            assert(lm.time_match_rate <= 1.0)
            if time_spirals * 2 / event_count >= SPIRAL_RATE :  #螺旋缠绕的双语
                lm.spiral = True
        self.BC.LANG_MODE = lm
        print('结束3-sub filer::analysis.')    
        return
    
    def get_BC(self) -> defs.build_controller :
        return self.BC

    def get_lang_mode(self) -> defs.SUB_EVENT_LANG_MODE :
        return self.BC.LANG_MODE
    
    def get_file_name(self) -> str :
        return self.file_name
    
    def is_same(self, other : sub_filer) -> bool :
        return self.file_name.lower() == other.file_name.lower()

    def is_bigb_sub(path_file : str) -> bool :
        BIGB_SUBS = ('.bigb.', '.bigbc.', '.bigbb.', )
        base_name = os.path.basename(path_file)
        pure_name = os.path.splitext(base_name)[0]
        for BS in BIGB_SUBS :
            if base_name.lower().find(BS) > 0 :
                return True
        if pure_name.upper().endswith('-CHT') :           #繁体字幕备份文件
            return True
        return False        

    def is_bigb(self) -> bool :
        return sub_filer.is_bigb_sub(self.file_name)
    
    #切换主字幕和次字幕
    def _switch_sub(self, LEVEL = 0) :
        print('开始进行主次字幕切换，总数={}...'.format(len(self.events)))
        cn = 0
        for event in self.events :
            if LEVEL == 0 :
                event.switch_chs_2_main()
                cn += 1
            elif LEVEL == 1 :
                event.switch_force(0)
                cn += 1
            else :
                print('下列事件未发生字幕切换...')
                event.print()
                pass
        if len(self.events) > 0 :
            print('主次字幕切换完成，切换/总数={}/{}。'.format(cn, len(self.events)))
        self.BC.switch_sub()
        return

    #调整双语字幕到合适的状态
    #如果需要切换则切换后返回TRUE
    def adjust_double_property(self) -> bool :
        adjusted = False
        print('开始检测是否需要主次字幕切换...')
        if self.get_BC().valid() :
            if self.get_BC().LM.need_switch(main = defs.SUB_LANG.CHINESE) :
                self._switch_sub(LEVEL = 0)
                adjusted = True
        return adjusted

