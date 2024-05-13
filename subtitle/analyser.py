import os

import defs

#分析字幕的语言（单语/双语/中/英）
def _analysis_ex(self, FullMode=False) :
    MIN_VALID_CHARS = 5
    DOUBLE_LANG_PERCENT = 0.3
    SINGLE_LANG_PERCENT = 0.7       
    DOUBLE_DEPART_PERCENT = 0.3
    #print('开始语言分析，event_count=%d.' %len(self.sub_events))
    if self.lang != 0 :
        return (self.lang, '已经完成检测。')   #已经被分析过，直接返回结果
    success = False
    if self.sub_events is None or len(self.sub_events) == 0 :
        self.lang = 0
        return (0, '没有事件数据。')

    #数据矫正
    self._detail_adjust()

    check_begin = 0
    check_lines = len(self.sub_events)
    if not FullMode :
        check_params = self.get_check_lang_begin_and_count()
        check_begin = check_params[0]
        check_lines = check_params[1]
    if check_lines == 0 :
        print('异常：检测数据行=0.')
        self.lang = -1
        return (self.lang, '有效数据行=0')
    result_list = []
    line_index = 0
    last_single = 0
    first_single = 0
    single_switch = 0
    #print('events数量=%d, check_begin=%d, check_count=%d.' %(len(self.sub_events), check_begin, check_lines))
    for i in range(len(self.sub_events)) :
        if i < check_begin :
            continue
        if i > check_begin + check_lines :
            break
        event = self.sub_events[i]
        if len(event.chs_text) < MIN_VALID_CHARS :
            #print('event i=%d被跳过。' %i)
            continue
        
        if event.ass_effect == 1 and event.is_XYZ_zero(IgnoreXYZ=self.ignore_XYZ) :          #特效数据行，不参与统计
            continue
        
        assert(isinstance(event.chs_text, str))
        assert(isinstance(event.eng_text, str))
        part1_lang = StrHandler.is_zh_or_eng(StrHandler.rip_srt_sub_closed_str(event.chs_text))
        if part1_lang <= 0 or part1_lang >= 3 :
            #zh_p = StrHandler.get_zh_percent(StrHandler.rip_srt_sub_closed_str(event.chs_text))
            #eng_p = StrHandler.get_eng_percent(StrHandler.rip_srt_sub_closed_str(event.chs_text))
            #print('异常：解析失败1，chs data=%s, 是中文(%.2f)也是英文(%.2f)。' %(event.chs_text, zh_p, eng_p))
            continue
            #assert(False)
        if event.eng_text == '' :       #单语事件
            if part1_lang == 1 :            #中文单语
                #print('中文单语：event chs=%s, raw=%s.' %(event.chs_text, event.raw_data))
                result_list.append(3)       #中文单语
                if first_single == 0 :
                    first_single = 3
                if last_single != 3 :
                    single_switch += 1
                    last_single = 3

            elif part1_lang == 2 :          #英文单语
                result_list.append(4)
                if first_single == 0 :
                    first_single = 4
                if last_single != 4 :
                    single_switch += 1
                    last_single = 4
        else :          #双语事件
            if len(event.eng_text) < MIN_VALID_CHARS :      #整个事件都不要
                continue
            part2_lang = StrHandler.is_zh_or_eng(StrHandler.rip_srt_sub_closed_str(event.eng_text))
            if part2_lang <= 0 or part2_lang >= 3 :
                #zh_p = StrHandler.get_zh_percent(StrHandler.rip_srt_sub_closed_str(event.eng_text))
                #eng_p = StrHandler.get_eng_percent(StrHandler.rip_srt_sub_closed_str(event.eng_text))
                #print('异常：解析失败4，eng data=%s, 既非中文(%.2f)也非英文(%.2f)。' %(event.eng_text, zh_p, eng_p))
                continue
            if part1_lang == 1 :
                if part2_lang == 1 :
                    #print('异常：事件的chs和eng都为中文，chs=%s, eng=%s.' %(event.chs_text, event.eng_text))
                    #assert(False)
                    continue
                elif part2_lang == 2 :
                    result_list.append(1)       #中英双语
                else :
                    continue
                    assert(False)
            elif part1_lang == 2 :
                if part2_lang == 2 :
                    continue
                    assert(False)
                elif part2_lang == 1 :
                    result_list.append(2)       #英中双语
                else :
                    continue
                    assert(False)
            else :
                assert(False)
    #print('事件解析完成，从(%d)个事件中共解析出(%d)个有效语言事件。' %(len(self.sub_events), len(result_list)))
    info_str = ''
    info_dict = dict()
    for type in result_list :
        str_type = str(type)
        if str_type not in info_dict :
            info_dict[str_type] = 1
        else :
            info_dict[str_type] += 1
        info_str += str(type)

    '''
    print('打印语言分析结果：')
    print(info_str)
    print('事件数量：%d, 翻转次数：%d。' %(len(result_list), single_switch))
    for e in self.sub_events :
        e.print()
        print('\n')
    '''
    
    type3_p = type4_p = 0
    for type in info_dict :
        p = float(info_dict[type] / len(result_list))
        #print('类型(%s)的占比=(%.2f%%).' %(type, p * 100))
        if type == '3' :
            type3_p = p
        if type == '4' :
            type4_p = p

        if p >= SINGLE_LANG_PERCENT :
            if type == '1' :        #中英双语
                self.lang = 3
            elif type == '2' :      #英中双语
                self.lang = 4
            elif type == '3' :      #中文单语
                self.lang = 1
            elif type == '4' :      #英文单语
                self.lang = 2
            break

        if type == '1' and p >= DOUBLE_LANG_PERCENT :
            self.lang = 3       #中英双语
            break
        elif type == '2' and p >= DOUBLE_LANG_PERCENT :
            self.lang = 4       #英中双语
            break
    if self.lang != 0 :         #已经检测出结果
        print('完成检测1，lang={}, info_str={}'.format(self.lang, info_str))
        return (self.lang, info_str)

    if len(result_list) > 0 and float(single_switch / len(result_list)) >= 0.7 :
        if first_single == 3 :
            self.lang = 5
        elif first_single == 4 :
            self.lang = 6 
        else :
            assert(False)
        print('完成检测2，lang={}, info_str={}'.format(self.lang, info_str))
        return (self.lang, info_str)

    #进一步检测分离模式
    if type3_p >= DOUBLE_DEPART_PERCENT and type4_p >= DOUBLE_DEPART_PERCENT :
        type3_p = type4_p = 0.0
        up_dict = dict()
        down_dict = dict()
        for i in range(len(result_list)) :
            if i <= len(result_list) / 2 :
                if str(result_list[i]) not in up_dict :
                    up_dict[str(result_list[i])] = 1
                else :
                    up_dict[str(result_list[i])] += 1
            else :
                if str(result_list[i]) not in down_dict :
                    down_dict[str(result_list[i])] = 1
                else :
                    down_dict[str(result_list[i])] += 1
        print('打印二次分析结果：')
        for type in up_dict :
            p = float(up_dict[type] / (len(result_list) / 2))
            print('类型(%s)在上半部的占比=(%.2f%%).' %(type, p * 100))
            if p >= SINGLE_LANG_PERCENT :
                print('上半部找到主要的单语=[%s].' %(type))
                if type == '3' :
                    type3_p = p
                elif type == '4' :
                    type4_p = p
                break
            
        for type in down_dict :
            p = float(down_dict[type] / (len(result_list) / 2))
            print('类型(%s)在下半部的占比=(%.2f%%).' %(type, p * 100))
            if p >= SINGLE_LANG_PERCENT :
                print('下半部找到主要的单语=[%s].' %(type))
                if type == '3' and type4_p >= SINGLE_LANG_PERCENT :
                    self.lang = 6
                elif type == '4' and type3_p >= SINGLE_LANG_PERCENT :
                    self.lang = 5
                break

    if self.lang == 0 :     #检测失败
        print('异常：检测失败，无法判断语言类型。')
        self.lang = -1
    else :
        print('完成检测3，lang={}, info_str={}'.format(self.lang, info_str))
    return (self.lang, info_str)