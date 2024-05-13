import os
import sys
import threading
import logging
from datetime import datetime

from asyncio.log import logger

def singleton(cls):
    _instance = {}
    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]
    return inner

@singleton
class MT_LOG(object) :
    #取得日志目录（不存在则创建目录）
    def comfirm_log_dir(self) -> str :
        cur_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        log_dir = os.path.join(cur_path, 'log')
        if not os.path.isdir(log_dir) :
            try :
                os.mkdir(log_dir)
            except Exception as e :
                err_info = "创建log目录(%s)失败，原因：%s." %(log_dir, str(e))
                #print(err_info)
                log_dir = ''
        return log_dir    
    def get_logger(self) -> logging.Logger :
        logger = logging.getLogger(self.get_task_name())
        return logger
    #生成任务的带路径日志名
    def get_task_lf_name(self) -> str :
        path_file = ''
        log_dir = self.comfirm_log_dir()
        self.lock.acquire()
        if log_dir != '' :
            file_name = self.get_task_name() + '.txt'
            path_file = os.path.join(log_dir, file_name)
        self.lock.release()
        return path_file
    #开始一个新任务的日志
    def begin_task(self, task_name : str, CLOSE_PREVIOUS : bool = False) -> bool :
        logged = False
        if CLOSE_PREVIOUS :
            self.end_task()

        self.lock.acquire()
        assert(self.fh is None)
        assert(self.task == '')
        self.task = task_name
        self.time = datetime.now()
        if self.task != '' :
            path_file = self.get_task_lf_name()
            #logging.basicConfig(filename=path_log, format='[%(levelname)s: %(message)s]', level = logging.INFO, filemode='w+')
            self.fh = logging.FileHandler(path_file, 'w+', encoding='utf-8')
            self.fh.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter("[%(levelname)s] - %(message)s")
            self.fh.setFormatter(formatter)
            #将相应的handler添加在logger对象中
            #logger = logging.getLogger(MT_LOG.LOGGER_NAME)
            logger = self.get_logger()
            logger.setLevel(logging.DEBUG)
            logger.addHandler(self.fh)            
            logged = True
        self.lock.release()
        return logged
    #结束一个任务的日志
    def end_task(self) :
        self.lock.acquire()
        if self.fh is not None :
            assert(self.task != '')
            logger.removeHandler(self.fh)
            self.fh = None
            self.task = ''
        else :
            assert(self.task == '')
        self.lock.release()
        return
    #取得当前任务的唯一名称（两次运行同一任务，名称不同）
    def get_task_name(self) -> str :
        task_id = ''
        self.lock.acquire() 
        if self.task != '' :
            st = datetime.strftime(self.time, '%Y-%m-%d %H-%M-%S')
            task_id = '{}_{}'.format(self.task, st)
        self.lock.release()
        return task_id
    def __init__(self) :
        self.task = ''
        self.time = datetime.now()
        self.fh = None
        self.lock = threading.RLock()
        #日志目录
        self.dir = self.comfirm_log_dir()
        return

log_obj = MT_LOG()
