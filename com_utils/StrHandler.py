from __future__ import annotations
# -*- coding: UTF-8 -*-

import sys
import os
from datetime import datetime 
import re
import string
import pypinyin

#sys.path.append(".") 
#sys.path.append("..") 

try:
    import com_utils.langconv as langconv
except ImportError:
    import langconv

import enchant
import re
import difflib

OLD_WORD_MAP = ( ('実', '实'), ('亜', '亚'), ('桜', '樱'), ('咲', '笑'), ('嶋', '岛'), ('栞', '刊'), ('篠', '小'), ('笹', '屉'), ('澪', '零'), ('冨', '富'), ('瀬', '濑'), ('沢', '泽'), ('岡', '冈') , ('倖', '幸'), ('凪', '止'), ('広', '广'),  \
    ('歩', '步'), ('絵', '绘'), ('雫', '霞'), ('糸', '丝'), ('笹', '屉'), ('斉', '齐'), ('巻', '卷'), ('笕', '见'), ('砥', '抵'), ('槇', '滇'), ('槙', '滇'), ('樋', '通'), ('榊', '神'), ('榎', '加'), ('椿', '春'), ('滝', '龙'), ('眞', '真'), ('栄', '荣'), ('裏', '里'), \
    ('刈', '义'), ('槻', '规'), ('掛', '挂'), ('佐々木', '佐佐木') )

ENG_END_FLAGS = r'(\.|\?|\!|\")\s*'       #英文句子结尾符号：（.?!"）后面带N个空格

def name_chs_format(name : str) -> str :
    format = name
    for OL in OLD_WORD_MAP :
        format = format.replace(OL[0], OL[1])
    format = cht_to_chs(format)
    return format

def is_legal_eng_word(word : str) -> bool :
    legal = False
    d = enchant.Dict("en_US")
    legal = d.check(word)
    return legal

#检查英文短句大小写模式。
#1: 全小写（含第一个单词首字母大写）。2：全大写。0：每个单词的首字母大写。-1：未知。
#注：需要考虑特殊单词的全大写。
def check_eng_lu_mode(text : str) -> int :
    mode = -1
    all_alpha = 0
    all_upper = 0
    all_words = 0
    first_upper_words = 0         #首字母大写的单词数量
    sentence_fu_flag = 0     #句子首字母是否大写
    for c in text :
        if c.isalpha() :
            all_alpha += 1
            if sentence_fu_flag == 0 :
                sentence_fu_flag = 2 if c.isupper() else 1
            if c.isupper() :
                all_upper += 1
    if all_alpha == 0 :
        return -1
    if float(all_upper) / all_alpha >= 0.9 :
        return 2
    elif all_upper == 0 or (all_upper == 1 and sentence_fu_flag == 2):
        return 1
    SPLITERS_PATTERN = r'( |-|_|\.|\(|\)|\[|\])'
    SPLITERS = (' ', '-', '_', '.', '(', ')', '[', ']', )
    words = re.split(SPLITERS_PATTERN, text)
    for w in words :
        if w.strip() == '' or w.strip() in SPLITERS :
            continue
        if w[0].isalpha() :
            all_words += 1
            if w[0].isupper() :
                first_upper_words += 1
    if all_words == 0 :
        mode = -1
    else :
        if float(first_upper_words) / all_words >= 0.9 :
            mode = 0
        else :
            mode = 1
    return mode

#检查英文段落大小写模式。
#1: 全小写（含第一个单词首字母大写）。2：全大写。0：每个单词的首字母大写。-1：未知。
def check_eng_lu_mode_list(texts : list) -> int :
    mode = -1
    modes = list()
    for text in texts :
        modes.append(check_eng_lu_mode(text))
    if len(modes) == 0 :
        return -1
    if float(modes.count(2)) / len(modes) >= 0.9 :
        mode = 2
    elif float(modes.count(1)) / len(modes) >= 0.8 :
        mode = 1
    elif float(modes.count(0)) / len(modes) >= 0.7 :
        mode = 0
    else :
        mode = -1
    return mode

#生成英文歌曲的标题标准名称，每个单词的首字母大写
def gen_eng_audio_title(text : str) -> str :
    #ALL_LOWER_WORDS = ('a', 'an', 'the', 'in', 'on', 'from', 'above', 'and', 'but', 'oh', 'ah', 'be', 'will', 'to', 'is', )
    ALL_LOWER_WORDS = ('a', 'an', 'the', 'in', 'on', 'and', 'but', 'oh', 'ah', 'be', 'to', 'is', )
    ALL_UPPER_WORDS = ('TV', 'USA', 'DJ', 'U', )
    title = ''
    SPLITERS_PATTERN = r'( |-|_|\.|\(|\)|\[|\])'
    D = enchant.Dict("en_US")
    items = re.split(SPLITERS_PATTERN, text)
    for i in items :
        if i.strip() == '' :
            title += i
        else :
            if i.lower() in ALL_LOWER_WORDS :
                if title.strip() == '' :
                    title += i.capitalize()
                else :
                    title += i.lower()
            elif i.upper() in ALL_UPPER_WORDS :
                title += i.upper()
            else :
                legal = D.check(i)
                if legal :
                    title += i.capitalize()
                else :
                    title += i
    return title

#调整一句英文句子为合法的句子。首字母大写，别的标准英语单词小写，非标准单词保持不变。
def eng_sentence_adjust(sentence : str) -> str :
    COMMA_SPLITTER = ','
    WORD_SPLITTER = ' '
    CLOSED_FLAGS_BEGIN = ( '(', '[', )
    CLOSED_FLAGS_END = (')', ']', )
    syn = ''
    firsted = False     #已加入第一个单词（首字母大写）
    D = enchant.Dict("en_US")
    sl = sentence.split(COMMA_SPLITTER)     #分句
    for s in sl :
        wl = s.split(WORD_SPLITTER)         #分词
        for w in wl :
            cw = False
            w = w.strip()
            if w == '' :
                continue
            if w[0] in CLOSED_FLAGS_BEGIN and w[-1] in CLOSED_FLAGS_END :
                cw = True
            legal = D.check(w)
            #print('word={}, legal={}.'.format(w, legal))
            if legal :
                if not firsted :      #第一个单词
                    if len(w) == 1 :
                        w = w[0].upper()
                    else :
                        w = w[0].upper() + w[1:].lower() 
                else :
                    w = w.lower()
            else :      #不合法（特殊单词）则保持不变
                pass

            if syn == '' :
                syn = syn + w
            else :
                syn = syn + WORD_SPLITTER + w
            if not firsted and not cw :
                firsted = True
        syn = syn + COMMA_SPLITTER
    if len(syn) > 0 and syn[-1] == COMMA_SPLITTER :
        syn = syn[:-1]      #去掉最后多余的一个COMMA_SPLITTER
    return syn

#英文段落标准化。
def eng_paragraph_adjust(paragraph : str) -> str :
    format = ''
    sl = re.split(ENG_END_FLAGS, paragraph)
    for s in sl : 
        if s.strip() == '' : 
            continue
        if s in ENG_END_FLAGS : 
            format += s + ' '
        else :
            new = eng_sentence_adjust(s)
            format += new
    format = format.strip()
    return format

SINGLE_PHRASE_SPLITERS = ('-', '_', '.', ',', '，', '。', '+', '：', ':', )
SINGLE_PHRASE_CHS_SPLITERS = ('-', '_', '.', ',', '，', '。', '+', '：', ':', ' ', )

#是否英文分隔符
def is_eng_spliter(c : str) -> bool :
    return c in SINGLE_PHRASE_SPLITERS
#是否中文分隔符
def is_chs_spliter(c : str) -> bool :
    return c in SINGLE_PHRASE_CHS_SPLITERS
#是否英文或中文分隔符
def is_general_spliter(c : str) -> bool :
    return is_eng_spliter(c) or is_chs_spliter(c)
#检测头部或尾部是否存在分隔符（不包括空格）
def has_spliter(input : str, begin : bool) -> bool :
    found = False
    if not begin :
        input = input[::-1]
    for c in input :
        if c == ' ' : 
            continue
        else :
            found = is_general_spliter(c)
            break
    return found
#删除头部的所有分隔符
def del_begin_spliters(input : str) -> str :
    if input.strip() == '' or not has_spliter(input, True) :
        return input
    output = input
    while is_general_spliter(output[0]) :
        output = output[1:]
    return output
#删除尾部的所有分隔符
def del_end_spliters(input : str) -> str :
    if input.strip() == '' or not has_spliter(input, False) :
        return input
    output = input
    while is_general_spliter(output[-1]) :
        output = output[:-1]
        if len(output) == 0 :
            break
    return output
#删除头尾的所有分隔符
def del_spliters(input : str) -> str :
    return del_end_spliters(del_begin_spliters(input))

#检测other的文本是否实际和base一个意思（去除分隔符）
def is_same_info(base : str, other : str) -> bool :
    def _samed(t1 : str, t2 : str) -> bool :
        samed = t1.upper().strip() == t2.upper().strip()
        return samed
    samed = False
    samed = _samed(base, other)
    if not samed :
        samed = _samed(base, del_begin_spliters(other))
    if not samed :
        samed = _samed(base, del_end_spliters(other))
    if not samed :
        samed = _samed(base, del_spliters(other))
    return samed

#对无括号的句子进行短语分割
#lang=0，语言未知。lang=1，中文。lang=2，英文。lang=3，其它语言。
def split_phrase_without_brackets(input : str, lang=0) -> list :
    pieces = list()
    SPLITERS_MATCH = r'(-+|_+|\.+|,+|，+|。+|\++|：|:)'
    SPLITERS_CHS_MATCH = r'(-+|_+|\.+|,+|，+|。+|\++|：|:| )'
    if lang == 1 :
        infos = re.split(SPLITERS_CHS_MATCH, input)
        #print('chs split count={}.'.format(len(infos)))
    else :
        infos = re.split(SPLITERS_MATCH, input)             #英文不对空格分词
    cur = ''
    for info in infos :
        #print('info 1={}.'.format(info))
        if len(info) == 0 :
            continue
        if lang != 1 and info.strip() == '' :
            continue
        #print('info 2={}.'.format(info))
        if (lang != 1 and is_eng_spliter(info[0])) or (lang == 1 and is_chs_spliter(info[0])) :    #分割符
            if len(info) == 1 :     #标准的单个分割符
                pieces.append(cur)  #前词入库
                cur = ''
                pieces.append(info) #分割符入库

            else :      #多个连续的分割符，不做分割符处理，作为前词的连续
                cur += info
        else :
            cur += info
    if cur != '' :
        pieces.append(cur)
        cur = ''
    return pieces

#删除一个字符串左右的括号
#tuple[0]=括号中的数据，tuple[1]=括号对字符串，如('()')。即len(tuple[1])或者为0，或者为2.
def del_brackets(input : str) -> tuple :
    PATTERN = r'([(|\[|{|《|（])([\s\S]*)([)|\]|}|》|）])'
    infos = re.split(PATTERN, input)
    if len(infos) == 1 :        
        return (input, '')
    data = ''
    brackets = ''
    items = list()
    for i in infos :
        if i.strip() != '' :
            items.append(i)
    if len(items) == 3 and len(items[0]) == 1 and len(items[2]) == 1 :
        data = items[1]
        brackets = items[0] + items[2]
    else :
        data = input
        brackets = ''
    return (data, brackets)

PAIR_SPLITERS = (('(', ')'), ('[', ']'), ('{', '}'), ('<', '>'), ('（', '）'), ('【', '】'), ('《', '》'), )
#检查输入文本里的分隔符对关系
#input：待检查的文本。
#spliter：要检查的分隔符。
#返回=0，括号偶数匹配。>0，spliter多余的数量。<0，跟spliter对应的括号多余的数量。
#-100，输入的spliter参数异常。
def check_pair_spliters(input : str, spliter : str) -> int :
    result = -100
    is_left = True
    Pair = None
    for PS in PAIR_SPLITERS :
        if spliter == PS[0] or spliter == PS[1] :
            is_left = spliter == PS[0]
            Pair = PS
            result = 0
            break
    if result == 0 :        #输入合法
        for i in input :
            if i == Pair[0] or i == Pair[1] :
                if is_left :
                    if i == Pair[0] :
                        result += 1
                    else :
                        result -= 1
                else :
                    if i == Pair[0] :
                        result -= 1
                    else :
                        result += 1

    return result

def check_all_pair_spliters(input : str) -> tuple :
    matchs = list()
    for PS in PAIR_SPLITERS :
        result = check_pair_spliters(input, PS[0])
        matchs.append(result)
    return tuple(matchs)

BRACKET_PHRASE_SPLITERS = ('(', ')', '[', ']', '{', '}', '《', '》', '（', '）', )
#对字符串进行括号分组，返回的分组包括括号，类似'(test)'
def split_by_brackets(input : str) -> list :
    #SPLITERS = ('(', ')', '[', ']', '{', '}', '《', '》', '（', '）', )
    outputs = list()
    infos = re.split(r'([()|\[\]|{}|《》|（）])', input)
    begin_s = False
    cur = ''
    for info in infos :
        if info in BRACKET_PHRASE_SPLITERS :  #遇到分割符
            if not begin_s :     #开区间
                if cur.strip() != '' :
                    outputs.append(cur)  #之前的piece入库
                cur = info
                begin_s = True
            else :      #闭区间
                cur += info
                outputs.append(cur)
                cur = ''
                begin_s = False
        else :
            if begin_s :
                cur += info
            else :
                if info.strip() != '' :
                    outputs.append(info)
                cur = ''
    return outputs

class spliter_pos :
    def __init__(self, spliter : str = '', pos : int = -1) -> None :
        self.spliter = spliter   #分隔符
        self.pos = pos       #分隔符的起始位置
        return
    def valid(self) -> bool :
        return self.spliter != '' and self.pos >= 0
    def reset(self) :
        self.spliter = ''
        self.pos = -1
        return
    def begin(self) -> int :
        return self.pos
    def end(self) -> int :
        return self.pos + len(self.spliter)
    def len(self) -> int :
        return len(self.spliter)

#括号处理器
class bracket_group :
    BRACKET_SPLITERS = ( ('(', ')'), ('[', ']'), ('{', '}'), ('《', '》'), ('（', '）'), ('【', '】'), )
    #检查输入是否为左括号
    def is_left_bracket(c : str) -> bool :
        left = False
        for BS in bracket_group.BRACKET_SPLITERS :
            if c == BS[0] : #发现开始标志
                left = True
                break
        return left
    #检查输入是否为右括号
    def is_right_bracket(c : str) -> bool :
        right = False
        for BS in bracket_group.BRACKET_SPLITERS :
            if c == BS[1] : #发现开始标志
                right = True
                break        
        return right
    #查找和left_pos层级匹配的括号封闭符，找不到返回-1。
    def search_right_bracket(data : str, left_pos : int) -> int :
        right_pos = -1
        if left_pos < 0 or left_pos >= len(data) :
            return -1
        left_b = data[left_pos]
        right_b = ''
        for BS in bracket_group.BRACKET_SPLITERS :
            if left_b == BS[0] : #发现开始标志
                right_b = BS[1]
                break
        if right_b == '' :      #输入异常
            return -1
        stack = 0
        for i in range(len(data)) :
            if i <= left_pos :
                continue
            if data[i] == left_b :          #遇到开始括号
                stack += 1
            elif data[i] == right_b :       #遇到结束括号
                if stack == 0 :
                    right_pos = i
                    break
                else :
                    assert(stack > 0)
                    stack -= 1
        return right_pos
    #检查输入是否括号自洽
    #自洽条件：
    #条件1：以左括号开始，以右括号结束。
    #遇到嵌套的情况，同样满足条件1.
    def _is_consistent(bg : tuple, data : str) -> bool :
        value = 0
        for c in data :
            if c == bg[0] :
                value += 1
            elif c == bg[1] :
                value -= 1
            if value < 0 :
                break
        return value == 0
    #检查是否所有的括号都自洽
    def is_all_consistent(data : str) -> bool :
        success = True
        for bg in bracket_group.BRACKET_SPLITERS :
            success = bracket_group._is_consistent(bg, data)
            if not success :
                break
        return success
    #检查头尾字符是否为匹配的括号且自洽
    def is_BE_consistent(data : str) -> bool :
        success = False
        if len(data) == 0 :
            return False
        for BS in bracket_group.BRACKET_SPLITERS :
            if data[0] == BS[0] and data[-1] == BS[1] :
                success = bracket_group._is_consistent(BS, data)
                break
        return success
    def __init__(self, raw : str, stack : int = 0) -> None :
        self.begin = spliter_pos()
        self.end = spliter_pos()
        self.raw = raw       #begin和end之间的原始数据
        self.is_chs = False
        self.pieces = list()        #list里的元素可能为str, 也可能为bracket_group
        self.stack = stack              #堆栈层级
    def get_piece_count(self) -> int :
        return len(self.pieces)
    def get_stack(self) -> int :
        return self.stack
    def prepare(self) :
        self.is_chs = is_lang_zh(self.raw, Percent=0.1)
        for piece in self.pieces :
            if isinstance(piece, bracket_group) :
                piece.prepare()
        return
    def link(self) -> str :
        info = ''
        for piece in self.pieces :
            if isinstance(piece, tuple) :
                if piece[0].strip() != '' :
                    info += ' ' + piece[0]
            elif isinstance(piece, bracket_group) :
                info += ' ' + piece.link()
            else :
                assert(False)
        info = info.strip()
        if info != '' and self.begin.valid() :
            info = self.begin.spliter + info + self.end.spliter
        return info
    def pprint(self) -> str :
        info = ''
        if self.begin.valid() :
            info += 'bs={}, es={}.'.format(self.begin.spliter, self.end.spliter)
        for piece in self.pieces :
            if isinstance(piece, tuple) :
                info += '-' + piece[0] + '-'
            elif isinstance(piece, bracket_group) :
                info += 'g-' + piece.pprint() + '-g'
            else :
                assert(False)
        return info
    #对piece操作
    #handlers为外部函数集合
    def piece_update(self, handlers : list) :
        PRINTED = False
        for i in range(len(self.pieces)) :
            piece = self.pieces[i]
            if isinstance(piece, tuple) : 
                if piece[1] == 1 :      #fixed
                    continue
                if PRINTED :
                    print('\n开始对分组{}进行分片处理...'.format(piece[0]))
                new_piece = ''
                words = split_phrase_without_brackets(piece[0], 1 if self.is_chs else 0)
                ignored = False     #WORD是否被去除，用过去除相关的分隔符
                for j in range(len(words)) :
                    temp = words[j]
                    if PRINTED :
                        print('index={}/{}, item={}, ignored={}'.format(j, len(words), temp, ignored))
                    
                    if temp == '' :     #to do : 检查后遗症
                        continue
                    if temp.strip() == '' :
                        if PRINTED :
                            print('当前片段为空格组，len={}.'.format(len(temp)))
                        if ignored :        #上一个WORD被忽略
                            continue    
                    is_SP = is_general_spliter(temp.strip())
                    if PRINTED :
                        print('处理片段={}, is_SP={}'.format(temp, is_SP))
                    if is_SP :      #分隔符
                        if ignored :
                            temp = ''
                            ignored = False
                            if PRINTED :
                                print('ignore复位0')
                    else :
                        for handler in handlers :
                            if PRINTED :
                                print('片段func name={}'.format(handler.__name__))
                            info = handler(temp, False, self)
                            if PRINTED :
                                print('片段func处理结束，input={}, outout={}, fixed={}'.format(temp, info[1], info[0]))
                            if info[1] != temp :    #发生了更新
                                if PRINTED :
                                    print('片段({}/{})update, replace ({}) 2 ({})'.format(j, len(words), temp, info[1]))
                                temp = info[1]
                                if temp.strip() == '' :
                                    ignored = True
                                    if PRINTED :
                                        print('ignore置位')
                                else :
                                    ignored = False
                                    if PRINTED :
                                        print('ignore复位1')
                                if j + 1 == len(words) :  #最后一个word
                                    if PRINTED :
                                        print('删除头部分隔符, data={}'.format(temp))
                                    temp = del_begin_spliters(temp)
                                else :                      
                                    if PRINTED :
                                        print('删除尾部分隔符，data={}'.format(temp))
                                    temp = del_end_spliters(temp)
                            else :
                                ignored = False
                                if PRINTED :
                                    print('ignore复位2')

                            if info[0] :        #fixed输出
                                break

                    new_piece += temp
                    if PRINTED :
                        print('片段累加piece的字符串={}'.format(new_piece))

                if new_piece != piece :
                    if ignored :    #最后一个WORD被忽略
                        new_piece = del_end_spliters(new_piece)     #删除最后的分隔符（有的话）
                    #new_piece = del_spliters(new_piece)     #删除两边的分隔符
                    if PRINTED :
                        print('片段更新值为{}'.format(new_piece))
                    self.pieces[i] = (new_piece, self.pieces[i][1])
                else :
                    if PRINTED :
                        print('片段值=({}) 未改变。'.format(piece))
                    pass
            elif isinstance(piece, bracket_group) :
                piece.piece_update(handlers)
            else :
                assert(False)
        return
    #整个group操作
    #handlers为外部函数集合
    def group_update(self, handlers : list) :
        PRINTED = False
        for i in range(len(self.pieces)) :
            piece = self.pieces[i]
            if isinstance(piece, tuple) : 
                if piece[1] == 1 :      #fixed
                    continue        #不处理
                fixed = 0
                temp = piece[0]
                if PRINTED :
                    print('处理分组={}'.format(temp))
                for handler in handlers :
                    if PRINTED :
                        print('func name={}'.format(handler.__name__))
                    info = handler(temp, True, self)
                    if PRINTED :
                        print('分组func处理结束，input={}, outout={}, fixed={}'.format(temp, info[1], info[0]))
                    if info[1] != temp :
                        if PRINTED :
                            print('分组update, replace ({}) 2 ({})'.format(temp, info[1]))
                        temp = info[1]
                    if info[0] :        #fixed输出
                        fixed = 1
                        break
                if temp.strip() != piece[0].strip() or fixed == 1 :
                    if PRINTED :
                        print('数据({})有变更或fixed置位({})，删除分隔符...'.format(temp, fixed))
                    temp = del_spliters(temp)       #删除两边的分隔符
                    if PRINTED :
                        print('分组更新值为={}, fixed={}, raw={}.\n'.format(temp, fixed, piece[0]))
                    self.pieces[i] = (temp, fixed)
                else :
                    if PRINTED :
                        print('分组值=({}) 未改变。\n'.format(piece[0]))
                    pass
            elif isinstance(piece, bracket_group) :
                piece.group_update(handlers)
            else :
                assert(False)
        return

    def generation(input : str, stack : int) -> bracket_group :
        group = bracket_group(input, stack)
        input = input.strip()

        if bracket_group.is_left_bracket(input[0]) :
            right = bracket_group.search_right_bracket(input, 0)
            if right == len(input) - 1 :    #最后一个
                group.begin = spliter_pos(input[0], 0)
                group.end = spliter_pos(input[right], right)
                input = input[1:right]      #去头去尾

        last = cur = 0
        while cur < len(input) :
            if bracket_group.is_left_bracket(input[cur]) :
                #处理之前的数据
                before = input[last:cur]
                if before.strip() != '' :
                    group.pieces.append((before, 0))     #之前的数据片入库
                last = cur             
                #查找结束括号
                right = bracket_group.search_right_bracket(input, cur)
                if right > cur :  #找到匹配的结束符号
                    raw = input[cur:right + 1]    #包括结束括号i
                    sub_group = bracket_group.generation(raw, stack + 1)
                    group.pieces.append(sub_group)
                    last = cur = right + 1
                else :
                    cur += 1
            else :
                cur += 1        
        if last != cur :
            assert(last < cur)
            before = input[last:cur]
            if before.strip() != '' :
                group.pieces.append((before, 0))
            last = cur
        group.prepare()
        return group

#连接两个字符串，去掉连接之间多余的分隔符
def link_str(str1 : str, str2 : str, SPLITERS = '') -> str :
    if str1.strip() == '' or str2.strip() == '' :
        return str1 + str2
    DEF_SPLITERS = '-.'
    if SPLITERS == '' :
        SPLITERS = DEF_SPLITERS
    output = ''
    pos1 = pos2 = -1
    for SPLITER in SPLITERS :
        pos1 = str1.rfind(SPLITER)
        if pos1 >= 0 :
            right = str1[pos1+1:]
            if right.strip() == '' :    #找到合法的分隔符
                break
            else :
                pos1 = -1
    for SPLITER in SPLITERS :
        pos2 = str2.find(SPLITER)
        if pos2 >= 0 :
            left = str2[:pos2]
            if left.strip() == '' :
                break
            else :
                pos2 = -1
    if pos1 >= 0 and pos2 >= 0 :    #两边都有分隔符
        #保留str1的分隔符
        output = str1 + str2[pos2+1:]
    else :
        output = str1 + str2
    output = ' '.join(output.split())
    return output

# 转换繁体到简体
def cht_to_chs(cht : str) -> str:
    #FIXED_WORDS = ( ('癡', '痴'), ('著', '着'), )  #左小诅咒4大名著异常
    FIXED_WORDS = ( ('癡', '痴'), ('讚', '赞'), ('崙', '仑'), )
    for FW in FIXED_WORDS :
        cht = cht.replace(FW[0], FW[1])
    #line = com_utils.langconv.Converter('zh-hans').convert(cht)
    line = langconv.Converter('zh-hans').convert(cht)
    line.encode('utf-8')
    return line

def _is_chs_or_eng(input : str) -> bool :
    failed = False
    for c in input :
        if ord(c) < 128 :
            continue
        elif is_char_chinese(c) :
            continue
        else :
            failed = True
            break
    return not failed

#判断一个字符串是否全部为英文
def is_pure_eng(input : str) -> bool :
    return all(ord(c) < 128 for c in input)

#字符串包含日文
def is_contains_jap(input : str) -> bool :
    jap = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]') 
    return jap.search(input) != None

#字符串包含日文
def is_contains_korean(input : str) -> bool :
    jap = re.compile(r'[\uAC00-\uD7A3]') 
    return jap.search(input) != None    

#字符串包含日韩文
def is_contains_JK(input : str) -> bool :
    return is_contains_jap(input) or is_contains_korean(input)

def is_ascii_controler(c : str) -> bool :
    controler = False
    if ord(c) >= 0 and ord(c) <= 64 :
        controler = True
    elif ord(c) >= 91 and ord(c) <= 96 :
        controler = True
    elif ord(c) >= 123 and ord(c) <= 127 :
        controler = True
    return controler

def is_symbol(c : str) -> bool :
    symbol = False
    ENG_SYMBOL = string.punctuation
    CHS_SYMBOL = '！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.。'
    if c in ENG_SYMBOL :
        symbol = True
    elif c in CHS_SYMBOL :
        symbol = True
    return symbol

def is_char_chinese(c : str) -> bool :
    ZH_SYMBOLS = '！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.。'
    is_zh = False
    if '\u4e00' <= c <= '\u9fa5' :
        is_zh = True
    elif c in ZH_SYMBOLS :
        is_zh = True
    return is_zh

#字符串全部为中文
def is_all_chinese(input : str) -> bool :
    for _c in input:
        if not is_char_chinese(_c) :
            return False
    return True

#字符串包含中文
def is_contains_chinese(input : str) -> bool :
    for _c in input:
        if '\u4e00' <= _c <= '\u9fa5':
            return True
    return False    

#取得一个字符串中的英文比重，0-100
#100个字符里有1个英文字符，返回1. 100个字符里有100个英文字符，返回100。
def get_eng_percent(input : str) -> int :
    percent = 0
    count = len(input)
    eng_count = 0
    for c in input :
        if is_ascii_controler(c) :
            count -= 1
        elif (ord(c) >= 65 and ord(c) <= 90) or (ord(c) >= 97 and ord(c) <= 122) :
            eng_count += 1
    if count > 0 :
        percent = int(eng_count * 100 / count)
    #print('len=%d, count=%d, eng=%d.' %(len(str), count, eng_count))
    return percent    

#取得一个字符串中的中文比重，0-100
#100个字符里有1个中文字符，返回1. 100个字符里有100个中文字符，返回100。
def get_zh_percent(input : str) -> int :
    percent = 0
    count = len(input)
    zh_count = 0
    for c in input :
        if is_ascii_controler(c) :
            count -= 1              #控制字符不计入分母
        elif is_char_chinese(c) :
            zh_count += 1
    if count > 0 :
        percent = int(zh_count * 100 / count)
    #print('len=%d, count=%d, zh=%d.' %(len(str), count, zh_count))
    return percent

#检测输入文本的语言。中文返回1，英文返回2，未知返回0.
def is_zh_or_eng(input : str) -> int :
    if is_lang_zh(input, Percent=0.3) :
        return 1
    elif is_lang_eng(input) :
        return 2
    return 0

def is_lang_zh(input : str, Percent=0.8) -> bool :
    if input.strip() == '' :
        return False
    return float(get_zh_percent(input) / 100) >= Percent

def is_lang_eng(input : str, Percent=0.95) -> bool :
    if input.strip() == '' :
        return False
    return float(get_eng_percent(input) / 100)>= Percent

def rip_ass_sub_closed(input : str) -> list :
    closed_table = {'}': '{', }
    return rip_str_closed(input, ClosedTable=closed_table)

def rip_ass_sub_closed_str(input : str) -> str:
    list = rip_ass_sub_closed(input)
    result = ''
    for l in list :
        result += l + ' ' 
    return result.strip()

def rip_srt_sub_closed(txt : str) -> list :
    closed_table = {'}': '{', '>': '<', }
    return rip_str_closed(txt, ClosedTable=closed_table)

def rip_srt_sub_closed_str(txt : str) -> str :
    list = rip_srt_sub_closed(txt)
    result = ''
    for l in list :
        result += l + ' ' 
    return result.strip()

#删除字符串里的闭包数据
def rip_str_closed(input : str, ClosedTable : dict=None) -> list :
    texts = list()
    CLOSE_DICT = {'}': '{', '>': '<', ']' : '[', ')' : '(', }
    if ClosedTable == None :
        ClosedTable = CLOSE_DICT
    begin = end = -1
    cps = []        #check points 
    for i in range(len(input)) :
        c = input[i]
        if c in ClosedTable.values() : #闭包开始标志
            if len(cps) == 0 :  #遇到一个最外层的开始标志
                #assert(begin >= 0)
                #print('find first closed, i=(%d), begin=(%d).' %(i, begin))
                if begin >= 0 :
                    text = input[begin:i]
                    #print('i=(%d), begin=(%d), text=(%s).' %(i, begin, text))
                    if text.strip() != '' :
                        texts.append(text)
                begin = -1
            cps.append(c)
        elif c in ClosedTable :      #闭包结束标志
            #print('find closed right, i=%d, begin=%d. before char=%s.' %(i, begin, str[i-1]))
            if len(cps) == 0 :      #没有开始标志，直接出来一个结束标志
                #assert(False)
                pass
            elif cps.pop() != ClosedTable[c] :   #跟最后一个压入的开始标志不匹配
                #闭合异常
                #assert(False)
                pass
        else :      #遇到普通字符
            if len(cps) == 0 and begin == -1 :
                begin = i
                #print('normal char=(%s), set begin from -1 to i=(%d).' %(c, i))

    #print('last begin=%d, len(cps)=%d...' %(begin, len(cps)))
    #if begin >= 0 and (begin+1) < len(str) :
    if begin >= 0 and (begin) < len(input) :
        text = input[begin:]
        #print('last check, begin=(%d), text=(%s).' %(begin, text))
        if text.strip() != '' :
            texts.append(text)
    if len(cps) != 0 :      #闭包没有遇到足够的关闭标志
        #assert(False)
        pass
    return texts

#判断字符串是否闭合
def is_str_closed(input : str) -> bool :
    CLOSE_DICT = {'}': '{', '>': '<', ']' : '[', ')' : '(', }
    b = []
    for c in input:
        if c in CLOSE_DICT.values() :
            b.append(c)
        elif c in CLOSE_DICT.keys() :
            if len(b) == 0 or b.pop() != CLOSE_DICT[c]:
                return False
    #判断最后列表b里面的左括号是否全部被弹出
    if len(b) != 0 :
        return False
    return True

#取得字符串中第N个分隔符出现的位置
def get_N_index(info_str : str, spliter : str, n : int) -> int:
    index = -1
    if n <= 0 :
        return -1
    count = 0
    begin = 0
    while True :
        index = info_str.find(spliter, begin)
        if index < 0 :
            break
        else :
            begin = index + 1
            count += 1
            if count >= n :
                break    
    return index

#删除一个字符串里的指定字符
#如esc_list=None，则删除字符串里的回车换行
def str_escape(input : str, esc_list=None) -> str:
    DEFAULT_ESCAPE_LIST = ('\\n', '\\r', '\\r\\n', )
    if esc_list == None :
        esc_list = DEFAULT_ESCAPE_LIST
    new_str = input
    for e in esc_list :
        new_str = new_str.replace(e, '').replace(e.upper(), '')
    return new_str

#查找两个等长字符串的整数差异部分。
#如找到，返回差异部分的begin和end。没找到返回(-1, -1)
def find_num_diff(name1 : str, name2 : str) -> tuple :
    info = (-1, -1)
    pos = -1
    begin = end = -1
    if len(name1) == len(name2) :
        for i in range(len(name1)):
            if name1[i] != name2[i] :       #第一个有差异的位置
                pos = i
                break
        if pos >= 0 and name1[pos].isdigit() and name2[pos].isdigit() :
            begin = pos
            while begin > 0 :
                if name1[begin-1].isdigit() and name2[begin-1].isdigit() :
                    begin -= 1
                else :
                    break
            end = pos 
            while end < len(name1) - 1 :
                if name1[end+1].isdigit() and name2[end+1].isdigit() :
                    end += 1
                else :
                    break
            tail = end + 1
            while tail < len(name1) :
                if name1[tail] == name2[tail] : #后面部分也必须相同
                    tail += 1
                else :      
                    begin = end = -1
                    break
            info = (begin, end+1)
    return info

def find_num_diffs(names : list) -> tuple :
    if len(names) < 2 :
        return (None, None)
    info = None     #有效为(begin, end)的tuple
    diffs = list()
    for i in range(len(names)) :
        base = names[i]
        for j in range(len(names)) :
            if i == j :
                continue
            cur = find_num_diff(base, names[j])
            if cur[0] >= 0 :       #找到
                if info is None :      #第一次
                    info = cur
                    diffs.append(base)
                    diffs.append(names[j])
                elif cur == info :
                    diffs.append(names[j])
        if info is not None :
            assert(len(diffs) > 1)
            break
        else :
            assert(len(diffs) == 0)        
    return (info, diffs)

#比较两个字符串是否有同样的开头
#如果有同样的开头, pos返回第一个不同位置。
#如果没有相同的开头，返回-1。
#如果两个字符串相同，返回0.
def is_same_header(s1 : str, s2 : str) -> int :
    pos = -1
    if s1 == s2 :
        return 0
    else :
        differ = difflib.Differ()
        diffs = differ.compare(s1, s2)    
        index = 0
        for diff in diffs :
            if diff[0] == '-' or diff[0] == '+' :
                if index == 0 :     #第一个字符就不一样
                    pos = -1 
                else :
                    pos = index
                break
            index += 1
    return pos

def is_same_tailer(s1 : str, s2 : str) -> int :
    #逆转
    rs1 = ''.join(reversed(s1))
    rs2 = ''.join(reversed(s2))
    pos = is_same_header(rs1, rs2)
    return pos

def is_same_headers(inputs : list) -> int :
    pos = -1
    if len(inputs) <= 1 :
        return -1
    s1 = inputs[0]
    for i in range(len(inputs)) :
        if i == 0 :
            continue
        s2 = inputs[i]
        tmp = is_same_header(s1, s2)
        #print('i={}, s1={}, s2={}, tmp={}, pos={}'.format(i, s1, s2, tmp, pos))
        if tmp <= 0 or (pos > 0 and tmp != pos) :
            if tmp <= 0 :
                return tmp
            else :
                return min(tmp, pos)
        elif pos == -1 :
            pos = tmp
        else :
            assert(pos == tmp)
            pass
    return pos

def is_same_tailers(inputs : list) -> int :
    r_inputs = list()
    for input in inputs :
        r_inputs.append(''.join(reversed(input)))
    pos = is_same_headers(r_inputs)
    return pos

#取得字符串列表相同的两端数据（返回左/右第一个不一样的字符，如开头就不同返回-1）
def get_same_ends(inputs : list) -> tuple :
    assert(isinstance(inputs, list))
    begin = is_same_headers(inputs)
    end = is_same_tailers(inputs)
    return (begin, end)

#比较两个字符串是否只有一个ascii码字符差异
#返回的tuple: (pos为差异的位置，name1的差异char1, name2的差异char2)。两个name相同pos返回-1，差异太大pos返回-2.
def find_one_char_diff(name1 : str, name2 : str) -> tuple :
    #'-'，包含在第一个序列中，但不包含在第二个序列中。
    #'+'，包含在第二个序列中，但不包含在第一个序列中。
    pos = -2
    fd = False
    c1 = ''
    c2 = ''
    if name1 == name2 :
        return (-1, '', '')
    elif len(name1) != len(name2) :
        return (-2, '', '')
    else :
        differ = difflib.Differ()
        diffs = differ.compare(name1, name2)
        #print('\n'.join(diffs))
        pos = 0
        for diff in diffs :
            if diff[0] == ' ' and (c1 == '' or c2 == '') :
                if (c1 == '' and c2 != '') or (c1 != '' and c2 == '') :
                    pos = -2 
                    break
                else :
                    pos += 1
            elif diff[0] == '-' :
                if c1 == '' :
                    c1 = diff[2]
                else :
                    pos = -2    #至少2个字符不同，差异太大
                    break
            elif diff[0] == '+' :
                if c2 == '' :
                    c2 = diff[2]
                else :
                    pos = -2
                    break
    #print('for end, pos={}, c1={}, c2={}.'.format(pos, c1, c2))
    if pos < 0 :
        return (pos, '', '')
    else :
        if c1 != '' and c2 != '' :              #只有一个差异字符
            if (c1.isdigit() and c2.isdigit()) or (c1.isalpha() and c2.isalpha()) :         #差异字符或者都是数字，或者都是字母
                return (pos, c1, c2)
            else :
                return (-2, '', '')

#查找列表中只有一个字符差异的元素
#返回tuple: 找到则[0]为差异字符的位置；[1]为符合一个字符差异的元素列表，元素[0]为name，元素[1]为差异字符。
#SORT=0，不排序。SORT=1，按ascii升序。SORT=2，按ascii降序。
def find_one_char_diffs(names : list, SORT : int = 0) -> tuple :
    def takeSecond(elem):   #取得列表的第二个元素
        return elem[1]

    one_diffs = list()
    pos = -1
    for n1 in names :
        one_diffs.clear()
        pos = -1
        for n2 in names :
            if n1 == n2 :
                continue
            info = find_one_char_diff(n1, n2)
            if info[0] >= 0 :   #找到n2和n1差异1个字符
                #print('pos({}) found diff, n1={}, n2={}.'.format(info[0], n1, n2))
                if pos == -1 :      #第一次找到
                    pos = info[0]
                    assert(len(one_diffs) == 0)
                    #加入n1
                    one_diffs.append((n1, info[1]))
                else :
                    if pos != info[0] : #这次找到和之前找到的差异字符位置不同
                        continue        #丢弃这个n2
                #加入n2
                one_diffs.append((n2, info[2]))
        if len(one_diffs) > 0 : #找到，结束处理
            assert(pos >= 0)
            break
    if (pos >= 0 and (SORT == 1 or SORT == 2)) :
        if SORT == 1 :  #升序
            one_diffs.sort(key=takeSecond)
        else :          #降序
            one_diffs.sort(key=takeSecond, reverse=True)
    return (pos, one_diffs)

#读入ini文件的一个session的全部行
def read_session(name : str, datas : list) -> list:
    lines = []
    push = False
    for data in datas :
        check = data.strip()
        if check.lower().find(name.lower()) == 0 :
            push = True
        elif len(check) >= 2 and check[0] == '[' and check[-1] == ']' :
            if push :
                break
        else :
            if push and check != '' :
                lines.append(data)
    return lines

def get_entity(info_str) :
    SPLIT_FALGS = (':', '：', )
    entity = info_str
    for SF in SPLIT_FALGS :
        index = entity.find(SF)
        if index >= 0 :
            entity = entity[index+1:]
            break
    entity = get_first_name(entity)
    return entity

#去除字符串中的所有回车和换行
def strip_RN(input : str) -> str :
    return input.replace('\n', '').replace('\r', '')

#去除字符串中所有的回车/换行和空格
def strip_all(input : str) -> str :
    return strip_RN(input).replace(' ', '')

#比较两个字符串去除空格后是否相同
#默认大小写不敏感，即INSENSITIVE = True
def same_exclude_space(first : str, second : str, IGNORE, INSENSITIVE = True) -> bool :
    first = first.replace(' ', '')
    second = second.replace(' ', '')
    if INSENSITIVE :
        first = first.lower()
        second = second.lower()
    return first == second

#检查是否有相同的子字符串
#返回的tuple[0], 相同的子串值，不存在则为''
#返回的tuple[1]，如指定了POS且子串的位置相同，返回起始位置。如位置不同则返回-1。
def check_samed(items : list, find_data : str) -> tuple : 
    SAME_PATTERN_T = (r'[(|（|\[|【]\s*({})\s*[)|）|\]|】]', r'\s+?({})\s+?', )
    same_data = ''
    same_pos = -1
    find_data = re.escape(find_data)
    for SPT in SAME_PATTERN_T :
        PN = SPT.format(find_data)
        same_data = ''
        same_pos = -1
        for item in items :
            info = re.search(PN, item, re.I)
            if info is None :
                #print('data no matched, reset 1, item={}'.format(item))
                same_data = ''  #复位
                same_pos = -1
                break
            else :
                #print('data matched, item={}'.format(item))
                if same_data == '' :
                    same_data = info.group(0)
                    assert(same_pos == -1)
                    same_pos = info.span()[0]
                    #print('first matched, same_data={}, same_pos={}'.format(same_data, same_pos))
                else :
                    assert(same_data == info.group(0))
                    if same_pos != -1 and same_pos != info.span()[0] : #位置不相同
                        #print('pos no matched, reset 2, old_pos={}, new_pos={}'.format(same_pos, info.span()[0]))
                        same_pos = -1       #复位
                        
        if same_data != '' :
            break
    return (same_data, same_pos)

#把一个包含名字信息的字符串转换成名字列表
def name_info_to_names(info_str) :
    names = []
    CHS_BRACKETS = ('（', '）', )
    ENG_BRACKETS = ('(', ')', )
    SPLIT_FLAGS = (',', '，', '、', '/', '|')
    br_index = -1
    bl_index = info_str.find(CHS_BRACKETS[0])
    if bl_index >= 0 :
        br_index = info_str.find(CHS_BRACKETS[1])
    else :
        bl_index = info_str.find(ENG_BRACKETS[0])
        if bl_index >= 0 :
            br_index = info_str.find(ENG_BRACKETS[1])
    if bl_index > 0 :
        names.append(info_str[:bl_index])
        extend_str = info_str[bl_index + 1 : br_index]
        handled = False
        for SF in SPLIT_FLAGS :
            if SF in extend_str :
                alias_list = extend_str.split(SF)
                names.extend(alias_list)
                handled = True
                break
        if not handled :
            names.append(extend_str)    
    else :
        handled = False
        for SF in SPLIT_FLAGS :
            if SF in info_str :
                alias_list = info_str.split(SF)
                names.extend(alias_list)
                handled = True
                break
        if not handled :
            names.append(info_str)
    return names

#取得一个包含名字信息的字符串里的第一个名字
def get_first_name(info_str) :
    first = ''
    name_list = name_info_to_names(info_str)
    if len(name_list) > 0 :
        first = name_list[0]
    return first

#取得一个字符串里的数字个数
def get_number_count(info_str) :
    count = 0
    for c in info_str :
        if c.isdecimal() :
            count += 1
    return count

def name_2_pinyin(name : str, trans_num : bool = False) -> str :
    IGNORE_ENG_SYMBOL = string.punctuation
    IGNORE_CHS_SYMBOL = '！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.。'
    DIGITAL_MAP = ( ('0', 'L'), ('1', 'Y'), ('2', 'E'), ('3', 'S'), ('4', 'S'), ('5', 'W'), ('6', 'L'), ('7', 'Q'), ('8', 'B'), ('9', 'J') )
    def del_ignore(name) :
        clean = name
        for ies in IGNORE_ENG_SYMBOL :
            clean = clean.replace(ies, '')
        for ics in IGNORE_CHS_SYMBOL :
            clean = clean.replace(ics, '')
        return clean
    def digital_2_pinyin(str) :
        py = str
        for DM in DIGITAL_MAP :
            py = py.replace(DM[0], DM[1])
        return py
    def _add_word(w, flag, wl) :
        clean = del_ignore(w).strip()
        if clean != '' :
            if flag == 3 :              
                if not clean.isupper() :    #混合大小写的英文单词，取首字母
                    clean = clean[0]
            wl.append((clean, flag))
        return
    def _name_2_frags(name) :
        frags = list()
        cur = ''
        flag = 0            #=1中文，=2数字，=3英文。=4其它语种。=0开头或丢弃字符，如标点符号。
        for i in range(len(name)) :
            c = name[i]
            if c.isdigit() :    #数字
                #print('find digital=%s.' %c)
                if flag == 2 :
                    cur = cur + c
                else :
                    if flag != 0 :
                        _add_word(cur, flag, frags)
                    cur = c
                    flag = 2
            #elif is_pure_eng(c) :   #英文字符
            elif c.encode().isalpha() :
                #print('find alpha=%s.' %c)
                if flag == 3 :
                    cur = cur + c
                else :
                    if flag != 0 :
                        _add_word(cur, flag, frags)
                    cur = c
                    flag = 3
            elif is_all_chinese(c) :         #中文字符
                #print('found chs=%s.' %c)
                if flag == 1 :
                    cur = cur + c
                else :
                    if flag != 0 :
                        _add_word(cur, flag, frags)
                    cur = c
                    flag = 1
            
            elif is_symbol(c) :              #无法识别的字符，如标点符号
                #print('found ignore char=%s.' %c)
                if flag != 0 :
                    _add_word(cur, flag, frags)
                    cur = ''
                    flag = 0
            else :          #无法识别的字符，日韩德等其它语种
                if flag == 4 :
                    cur = cur + c
                else :
                    if flag != 0 :
                        _add_word(cur, flag, frags)
                    cur = c
                    flag = 4
        if cur != '' and flag != 0 :            #最后一个词
            _add_word(cur, flag, frags)

        return frags

    py_list = list()
    frags = _name_2_frags(name)
    for f in frags :
        #print('data=%s, flag=%s.' %(f[0], f[1]))
        if f[1] == 1 :      #中文
            first_list = pypinyin.lazy_pinyin(f[0])
            first = ''
            for f in first_list :
                first += f[0].upper()
            py_list.append(first)
        elif f[1] == 2 :  #数字
            if trans_num :
                first = digital_2_pinyin(f[0])
            else :
                first = f[0]
            py_list.append(first)
        elif f[1] == 3 :    #英文
            first = f[0].upper()
            py_list.append(first)
        elif f[1] == 4 :    #其它语种，跟英语一样保留第一个字符
            first = f[0].upper()
            py_list.append(first)
    first_py = ''
    for py in py_list :
        first_py += py
    return first_py

#取得固定长度的拼音缩写
def get_fixed_PINYIN(data : str, fix_len : int) -> str :
    FULL_WITH = '0'
    fixed = ''
    assert(fix_len > 0)
    PY = name_2_pinyin(data)
    if len(PY) >= fix_len :
        fixed = PY[ : fix_len]
    else :
        fixed = PY.ljust(fix_len, FULL_WITH)
    return fixed

def test_get_n_index() :
    line = 'Dialogue: 0,0:02:04.20,0:02:06.28,Default,,0000,0000,0000,,我正在研究着什么?'
    index = get_N_index(line, ',', 9)
    print('pos of 9n = %d.' %(index))
    if index >= 0 and (index+1) < len(line) :
        print('next =(%s).' %(line[index+1]))
    return

def test_rip_str_closed() :
    MOVIES = ('索多玛120天.1974', '红色娘子军.1969', '悬疑', '三上悠亚', 'JULIA', '28.1999', )
    for m in MOVIES :
        is_chs = is_lang_zh(m)
        is_all = is_all_chinese(m)
        print('(%s)是否中文名=%s, %s.' %(m, is_chs, is_all))
    return

    str = '{{\\fn微软雅黑\\b1\\fs30\\shad0\\c&HB8A682&\\move(740,370,251,370)\\fade (255, 32, 224, 0, 500, 2000, 2200)}伯克利学校'
    str = '{\\pos(512.028,343.995)\\shad0\\c&H15191B&\\frz1.137\\3c&H404040&\\fn黑体\\fs30\\frx32\\fry0}2号摄像机'
    print('raw data=(%s).' %str)
    result = rip_srt_sub_closed_str(str)
    print(result)
    return


    now_t = datetime.now()
    str_now = datetime.strftime(now_t, '%H-%M-%S') 
    out_file = open('字幕信息' + str_now + '.txt', 'w+', encoding='utf-8')
    sys.stdout = out_file  #标准输出重定向至文件


    SRT_LINES = ('{\\fnMicrosoft YaHei\\fs17\\bord1\\shad1\\b0}来了  你要香肠  你要鸡蛋{\\r}{\\c&H62a8eb&\\fs13}if they wanna make out an exchange for a story.', \
        '{\\fnTahoma\\fs8\\bord1\\shad1\\1c&HC2E0EC&\\b0}Here you go. You got the sausage, pancakes for you,{\\r}', \
        '<font color=#ED935E>{\\fn微软雅黑\\fs25}热力来袭！', '<font><异常闭包{font size}迪尔茨', )
    for sl in SRT_LINES :
        print('原始行=(%s)...' %sl)
        texts = rip_str_closed(sl)
        print('萃取出%d个数据。' %(len(texts)))
        for t in texts :
            print('---数据：%s.' %(t))
    return

def test() :
    text = r'Casablanca. Bogie.\N{\fn宋体\fs20\shad1\4a&H50&\3c&HFF8000&\4c&HFF8000&}{\r}'
    info = rip_ass_sub_closed_str(text)
    print(info)
    return
    text = '拿破崙'
    #text = '黃1黄2黃3'
    chs = cht_to_chs(text)
    print(chs)
    return

    text = '我们[你们][1]'
    end = 1
    print('right={}'.format(text[-end:]))
    print('left={}'.format(text[:-end]))

    text = '我们[你们][1].flac'
    end = 6
    print('right={}'.format(text[-end:]))
    print('left={}'.format(text[:-end]))    
    return



    t1 = '孙燕姿 - The moment_CD1 - 01.不能和你一起.flac'
    t2 = '孙燕姿 - The moment_CD1 - 02.永远.flac'
    t2 = '孙燕姿 - The moment_CD1 - 01.不能和你一起.flac'
    pos = is_same_header(t1, t2)
    print('pos={}'.format(pos))
    if pos > 0 :
        print('t1 diff pos={}'.format(t1[pos]))
        print('t2 diff pos={}'.format(t2[pos]))
    return

    info = '[o(我们 的 【方向 】号码 )走吧]别'
    group = bracket_group.generation(info, 0)
    info = group.link()
    #info = group.pprint()
    print(info)
    return

    print('{}'.format(is_pure_eng(info)))
    return
    name1 = 'CD1'
    name2 = 'CD2'
    info = find_num_diff(name1, name2)
    print('diff result, begin={}, end={}.'.format(info[0], info[1]))
    if info[0] >= 0 :
        print(name1[info[0]:info[1]])
    return
    dir = 'Y:\\MUSES\\迪斯科\\(Italo-DiscoEuro-DiscoHi-NRGDisco) VA - All Stars Disco (22CD)1998-2000 FLAC'
    dir = 'Y:\\MUSES\\迪斯科\\猛士的士高(10CD)\\猛士的士高(10CD).flac'
    items = os.listdir(dir)
    info = find_num_diffs(items)
    if info[0] is None :
        print('未找到符合规律的子目录。')
    else :
        pos = info[0]
        print('找到差异部分，begin = {}, end = {}.'.format(pos[0], pos[1]))
        for i in info[1] :
            serial = str(i[pos[0]:pos[1]])
            assert(serial.isdigit())
            print('差异目录={}，序号={}.'.format(i, serial))
    return



    DIRS_NAME = ('1987-刘美君 LPCD45', )
    for dir_name in DIRS_NAME :
        print('\ninput=({})...'.format(dir_name))
        infos = split_phrase_without_brackets(dir_name, 1)
        for info in infos :
            print('output piece=({}).'.format(info))
    return

    print(ord('1'))
    print(ord('a'))
    print(ord('A'))
    print(chr(49))
    return
    '''
    name1 = 'CD1'
    name2 = 'C2D'
    info = find_one_char_diff(name1, name2)
    if info[0] >= 0 :
        print('found diff pos={}, c1={}, c2={}.'.format(info[0], info[1], info[2]))
    else :
        print('not found one char diff.')
    return
    '''
    NAMES = ('CD2', 'CD3', 'cover', 'CD1', )
    info = find_one_char_diffs(NAMES, SORT=2)
    if info[0] < 0 :
        print('not found one char diff.')
    else :
        print('found diff items, pos={}.'.format(info[0]))
        diffs = info[1]
        for diff in diffs :
            print('found diff item={}, diff={}.'.format(diff[0], diff[1]))
    
    return

    eng_data = '[Nancy] BOY, I COULD NEVER GET USED TO TREATMENT LIKE THAT? WHEN THE WIND BLOWS, EVERYTHING KIND OF CREAKS!'
    result = eng_paragraph_adjust(eng_data)
    print(result)
    return


    s = 1
    e = 13
    
    info = 'S{:0>2d}E{:0>2d}'.format(s, e)
    print(info)
    jap2 = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7A3]')  # \uAC00-\uD7A3为匹配韩文的，其余为日文

    NAMES = ('1984我爱，你ER', 'E.T', '做个勇敢中国', '大侦探波洛', 'The.Tragedy.of.Macbeth', '26种死法', '二十一克', '돌아오라 개구리소년', '東京リベンジャーズ', 'Händler der vier Jahreszeiten', )

    #NAMES = ('돌아오라 개구리소년', )
    for n in NAMES :
        py = name_2_pinyin(n)
        fix_3 = get_fixed_PINYIN(n, 3)
        print('名称=%s, 拼音=%s, 定长=%s.' %(n, py, fix_3))
    return

#test_get_n_index()
#test_rip_str_closed()
#test()