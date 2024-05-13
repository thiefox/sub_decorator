# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
import configparser

#from PyQt5 import QtWidgets
#import tkinter
#import tkinter.messagebox

class bba_config :
    INI_FILE_NAME = 'bba.ini'
    SECTION_GENERAL = 'GENERAL'
    GENERAL_KEY_LEVEL = 'LEVEL'
    GENERAL_KEY_ARTIST = 'ARTIST'
    GENERAL_KEY_ALIASES = 'ARTIST_ALIAS'
    GENERAL_KEY_ALBUM = 'ALBUM'
    GENERAL_KEY_CD_COUNT = 'CD_COUNT'

    SECTION_SUBDIRS = 'SUBDIRS'

    SECTION_AUDIOS = 'AUDIOS'
    AUDIOS_KEY_NAME_FIXED = 'NAME_FIXED'
    AUDIOS_KEY_NAME_MODE = 'NAME_MODE'
    AUDIOS_KEY_NAME_SPLITER = 'ARTIST_TITLE_SPLITER'
    def load_config(path_dir : str) -> bba_config :
        config = bba_config()
        if not config.load(path_dir) :
            config = None
        return config
    def __init__(self) -> None :
        self.parser = configparser.ConfigParser()
        self.path_dir = ''
        self.level = 0
        self.artist = ''
        self.artist_alias = list()
        self.album = ''
        self.cd_count = 0
        self.name_fixed = False
        self.name_mode = 0
        self.artist_title_spliter = ''
        return
    def load(self, path_dir : str) -> bool :
        success = False
        ini_file = os.path.join(path_dir, bba_config.INI_FILE_NAME)
        if os.path.exists(ini_file) and os.path.isfile(ini_file) :
            self.parser.read(ini_file, encoding='utf-8')
            self.path_dir = path_dir
            self._read_param()
            success = True
        return success
    def name_updated(self) -> bool :
        if not self.name_fixed :
            self.name_fixed = True
            return True
        return False
    def save(self) -> bool :
        path_ini = os.path.join(self.path_dir, bba_config.INI_FILE_NAME)
        if os.path.exists(path_ini) and os.path.isfile(path_ini) :
            with open(path_ini, 'w', encoding='utf-8') as ini_file :
                self.parser.write(ini_file)
                return True
        return False

    def get_param(self, section_name, key_name, default='') -> str :
        value = default
        if self.parser.has_section(section_name) :
                #print('found section={}'.format(section_name))
                value = self.parser.get(section_name, key_name)
                #print('key={}, value={}'.format(key_name, value))
                if value == '' :
                    value = default
        return value.strip()
    def get_list(self, section_name, key_name, SPLITTER='|') -> list :
        items = self.get_param(section_name, key_name).split(SPLITTER)
        valid_items = []
        for i in items :
            if i.strip() != '' :
                valid_items.append(i.strip())
        return valid_items
    def _read_param(self) :
        value = self.get_param(bba_config.SECTION_GENERAL, bba_config.GENERAL_KEY_LEVEL)
        if value.isdigit() :
            self.level = int(value)
        self.artist = self.get_param(bba_config.SECTION_GENERAL, bba_config.GENERAL_KEY_ARTIST)
        self.album = self.get_param(bba_config.SECTION_GENERAL, bba_config.GENERAL_KEY_ALBUM)
        self.artist_alias = self.get_list(bba_config.SECTION_GENERAL, bba_config.GENERAL_KEY_ALIASES)
        value = self.get_param(bba_config.SECTION_GENERAL, bba_config.GENERAL_KEY_CD_COUNT)
        if value.isdigit() and int(value) > 1 :
            self.cd_count = int(value)
        value = self.get_param(bba_config.SECTION_AUDIOS, bba_config.AUDIOS_KEY_NAME_FIXED)
        if value.isdigit() and int(value) == 1 :
            self.name_fixed = True
        value = self.get_param(bba_config.SECTION_AUDIOS, bba_config.AUDIOS_KEY_NAME_MODE)
        #print('name mode=({})'.format(value))
        if value.isdigit() :
            self.name_mode = int(value)
        self.artist_title_spliter = self.get_param(bba_config.SECTION_AUDIOS, bba_config.AUDIOS_KEY_NAME_SPLITER)
        return


class bigma_config :
    INI_FILE_NAME = 'sub_decorator.ini'
    SECTION_GLOBAL = 'GENERAL'
    GLOBAL_KEY_BIGA_DIRS = 'BIGA_DIRS'
    GLOBAL_KEY_4K_DIR = 'BIGA_4K_DIR'
    GLOBAL_KEY_LEAKED_DIR = 'BIGA_LEAKED_DIR'
    GLOBAL_KEY_NEWGF_DIR = 'BIGA_NEWGF_DIR'
    GLOBAL_KEY_BIGB_DIRS = 'BIGB_DIRS'

    SECTION_SUBTITLE = 'SUBTITLE'
    SUBTITLE_KEY_HISTORY_DIRS = 'HISTORY_DIRS'
    SUBTITLE_KEY_TV_DIR = 'TV_DIR'
    SUBTITLE_KEY_FORCE_REBUILD = 'FORCE_REBUILD'
    SUBTITLE_KEY_CHT_TO_CHS = 'CHT_TO_CHS'
    SUBTITLE_KEY_BEST_CHS_FONT = 'BEST_CHS_FONT'            #最佳的中文字体
    SUBTITLE_KEY_BEST_ENG_FONT = 'BEST_ENG_FONT'            #最佳的英文字体

    SECTION_AVINFO = 'AVDATA'
    AVINFO_KEY_HISTORY_DIRS = 'HISTORY_DIRS'

    SECTION_AUDIO = 'AUDIO'
    AUDIO_KEY_HISTORY_DIRS = 'HISTORY_DIRS'
    
    def __init__(self) :
        #print('bigma_config init calling...')
        self.parser = configparser.ConfigParser()
        self.load(bigma_config._get_default_ini())
        return
    def _get_default_ini() :
        cur_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        ini_file = os.path.join(cur_path, bigma_config.INI_FILE_NAME)         #读取到本机的配置文件
        return ini_file
    def load(self, file_name : str) :
        if os.path.isfile(file_name) :       
            self.parser.read(file_name, encoding='utf-8')
        return
    def save(self, file_name='') :
        if file_name == '' :
            file_name = bigma_config._get_default_ini()
        with open(file_name, 'w', encoding='utf-8') as ini_file :
            self.parser.write(ini_file)
        return
    def get_param(self, section_name : str, key_name : str, default='') -> str :
        value = default
        #if self.parser.has_section(section_name) :
        if self.parser.has_option(section_name, key_name) :
            value = self.parser.get(section_name, key_name)
            if value == '' :
                value = default
        return value
    def get_subtitle_best_chs_font(self) -> str :
        return self.get_param(bigma_config.SECTION_SUBTITLE, bigma_config.SUBTITLE_KEY_BEST_CHS_FONT)
    def get_subtitle_best_eng_font(self) -> str :
        return self.get_param(bigma_config.SECTION_SUBTITLE, bigma_config.SUBTITLE_KEY_BEST_ENG_FONT)
    def set_param(self, section_name : str, key_name : str, value : str) :
        if not self.parser.has_section(section_name) :
            self.parser.add_section(section_name)
        self.parser.set(section_name, key_name, value)
        return

    def get_dirs(self, section_name : str, key_name : str, SPLITTER='|') -> list:
        items = self.get_param(section_name, key_name).split(SPLITTER)
        dirs = list()
        for dir in items :
            dir = dir.strip()
            if os.path.isdir(dir) :
                dirs.append(dir)
        return dirs    
    def set_dirs(self, section_name : str, key_name : str, dirs : list, SPLITTER='|', MAX_COUNT=-1) :
        value = ''
        count = 0
        for dir in dirs :
            if MAX_COUNT >= 0 and count >= MAX_COUNT :      #达到最大数量
                break
            #normal = os.path.normcase(dir)
            normal = dir
            if value.upper().find(normal.upper()) >= 0 :        #重复元素
                continue
            if os.path.isdir(normal) :
                value += normal + SPLITTER
                count += 1
        self.set_param(section_name, key_name, value)
        return
    def load_actress_dirs(self) :
        ignore_name = {'images', 'gallery', 'extrafanart', 'tmp', 'temp', }
        actor_dict = {}        #创建字典
        j4k_dir = self.get_param(bigma_config.SECTION_GLOBAL, bigma_config.GLOBAL_KEY_4K_DIR)
        if j4k_dir != '' and os.path.isdir(j4k_dir) :
            assert(bigma_config.GLOBAL_KEY_4K_DIR not in actor_dict)
            actor_dict[bigma_config.GLOBAL_KEY_4K_DIR] = j4k_dir
        leaked_dir = self.get_param(bigma_config.SECTION_GLOBAL, bigma_config.GLOBAL_KEY_LEAKED_DIR)
        if leaked_dir != '' and os.path.isdir(leaked_dir) :
            assert(bigma_config.GLOBAL_KEY_LEAKED_DIR not in actor_dict)
            actor_dict[bigma_config.GLOBAL_KEY_LEAKED_DIR] = leaked_dir    
        newgf_dir = self.get_param(bigma_config.SECTION_GLOBAL, bigma_config.GLOBAL_KEY_NEWGF_DIR)
        if newgf_dir != '' and os.path.isdir(newgf_dir) :
            assert(bigma_config.GLOBAL_KEY_NEWGF_DIR not in actor_dict)
            actor_dict[bigma_config.GLOBAL_KEY_NEWGF_DIR] = newgf_dir    

        dirs = self.get_dirs(bigma_config.SECTION_GLOBAL, bigma_config.GLOBAL_KEY_BIGA_DIRS)

        for dir in dirs :
            if os.path.isdir(dir) :
                for p, ds, fs in os.walk(dir) :
                    for d in ds :
                        if d.lower() in ignore_name :
                            continue
                        path = os.path.join(p, d)
                        if path.upper().find(j4k_dir.upper()) >= 0 or path.upper().find(leaked_dir.upper()) >= 0 :
                            continue
                        names = rip_names_from_dir_name(d)
                        for name in names :
                            if name not in actor_dict :
                                actor_dict[name] = path
                            else :
                                print('异常：艺人(%s)有多个目录。目录1：%s，目录2：%s.' %(name, actor_dict[name], path))

        #print('由目录名萃取艺人名字典共载入(%d)条数据。' %(len(actor_dict)))
        return actor_dict

def like_normal_actor_name(str) :
    count = 0
    for c in str :
        if c.isdigit() :
            count += 1
    return len(str) >= 1 and count <= 1

#从AV仓库的目录名中萃取出艺人名列表（如欧美的双艺人视频，则提取失败）
def rip_names_from_dir_name(dir_name) :
    actor_names = []
    CHS_SPLIT_BEGINS = ('(', '（', )
    CHS_SPLIT_ENDS = (')', '）', )
    SPLITTERS = ('、', ',', '，', )
    str_info = dir_name

    begin = end = -1
    for sb in CHS_SPLIT_BEGINS :
        find = str_info.find(sb)
        if find >= 0 :
            begin = find
            break
    if begin >= 0 :
        for se in CHS_SPLIT_ENDS :
            find = str_info.find(se, begin)
            if find > 0 :
                end = find
                break
        if end == -1 :      #没有找到关闭符
            begin = -1
    if begin >= 0 and end > 0 :
        name = str_info[:begin]
        if like_normal_actor_name(name) :
            actor_names.append(name)
        others = str_info[begin+1:end]
        splitted = False
        for sp in SPLITTERS :
            names = others.split(sp)
            if len(names) > 1 :
                for name in names :
                    if like_normal_actor_name(name) :
                        actor_names.append(name)
                splitted = True
        if not splitted :
            if like_normal_actor_name(others) :
                actor_names.append(others)
    else :
        splitter = ''
        for sp in SPLITTERS :
            if str_info.find(sp) >= 0 :
                splitter = sp
                break
        if splitter == '' :             #单个艺人
            if like_normal_actor_name(str_info) :
                actor_names.append(str_info)

    return actor_names 

#全局对象
#config_obj = bigma_config()
