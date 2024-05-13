# -*- coding: utf-8 -*-
import os
import sys
import com_utils.config

bm_config = com_utils.config.bigma_config()
actress_dict = None

def get_actress_dict() :
    global actress_dict
    global bm_config
    assert(bm_config is not None)
    if actress_dict == None :
        actress_dict = bm_config.load_actress_dirs()
    return actress_dict

def get_data_path() -> str :
    cur_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    data_dir = os.path.join(cur_path, 'data')
    if not os.path.isdir(data_dir) :
        try :
            os.mkdir(data_dir)
        except Exception as e :
             err_info = "创建data目录(%s)失败，原因：%s." %(data_dir, str(e))
             print(err_info)
             data_dir = ''
    return data_dir

def get_log_path() -> str :
    cur_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    log_dir = os.path.join(cur_path, 'log')
    if not os.path.isdir(log_dir) :
        try :
            os.mkdir(log_dir)
        except Exception as e :
             err_info = "创建log目录(%s)失败，原因：%s." %(log_dir, str(e))
             print(err_info)
             log_dir = ''
    return log_dir    