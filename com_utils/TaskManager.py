# -*- coding: UTF-8 -*-

import sys
import os
import datetime
import threading

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import com_utils.multi_thread_loger

log = com_utils.multi_thread_loger.MT_LOG()

class Task_Impl_Base() :
    IGNORE_PROGRESS = 101
    CIRCLE_PROGRESS = -1
    def __init__(self) :
        self.task_mgr = None
        return
    def is_deal_item(self, path_name, is_dir) :
        return False
    def deal_with(self, path_name, is_dir) :
        if not self.is_deal_item(path_name, is_dir) :
            return 0
        return 1
    def get_log_name(self) :
        return 'BIGB日志'
    def pre_build(self, root_dir) -> bool :
        return True
    def post_build(self, root_dir, canceled) :
        return
    def notify(self, info, Percent=IGNORE_PROGRESS) :
        if self.task_mgr is not None :
            self.task_mgr.notify(info, Percent=Percent)
        return
    def set_task_mgr(self, task_mgr) :
        self.task_mgr = task_mgr
        return
    def get_task_mgr(self) :
        return self.task_mgr

class TaskJob(threading.Thread) :
    def __init__(self, *args, **kwargs) :
        super(TaskJob, self).__init__(*args, **kwargs)
        self.suspend_event = threading.Event()     # 用于暂停线程的标识
        #self.suspend_event.set()       # 设置为True
        self.running_event = threading.Event()      # 用于停止线程的标识
        #self.running_event.set()      # 将running设置为True

        self.root_dir = ''                           #处理根目录
        self.item_count = 0                     #根目录下的需要处理的视频文件数量
        self.current = 0

        self.impl_obj = None                #OO模式的处理器

        self.top_to_down = True                 #默认值

        self.notify_obj = None
        self.processor_notify = None
        self.finish_notify = None
        return

    def init_notify_info(self, obj, process, finish) :
        self.notify_obj = obj
        self.processor_notify = process
        self.finish_notify = finish
        return

    def init_deal_obj(self, obj, TopDown=True) :
        self.impl_obj = obj
        self.top_to_down = TopDown
        self.impl_obj.set_task_mgr(self)
        return

    def notify(self, info, Percent=Task_Impl_Base.IGNORE_PROGRESS) :        #Percent=101，单纯通知
        if self.notify_obj is not None and self.processor_notify is not None :
            if Percent == Task_Impl_Base.CIRCLE_PROGRESS :
                info = '-1|' + info    
            elif Percent >= 0 and Percent <= 100 :      #-1和100之外的数值，则单纯消息通知。
                info = str(Percent) + '|' + info
            self.processor_notify(self.notify_obj, info)
        return

    def prepare(self, root_dir) :
        self.root_dir = root_dir
        self.item_count = self.current = 0
        self.suspend_event.set()        #暂停线程信号
        self.running_event.set()        #取消线程信号
        return

    def calc_item_count(self) :
        self.item_count = 0
        for p, ds, fs in os.walk(self.root_dir) :
            for d in ds :
                path_name = os.path.join(p, d)
                if self.impl_obj is not None :
                    if self.impl_obj.is_deal_item(path_name, True) :
                        self.item_count += 1
            for f in fs :
                path_name = os.path.join(p, f)
                if self.impl_obj is not None :
                    if self.impl_obj.is_deal_item(path_name, False) :
                        self.item_count += 1
        if self.impl_obj is not None :
            if self.impl_obj.is_deal_item(self.root_dir, True) :
                self.item_count += 1
        return self.item_count

    #返回-1表示收到了提前退出信号，需要外层退出整个线程处理。
    #返回0为忽略元素，返回1为处理元素。
    def deal_one_item(self, path_name, is_dir) :
        #print('开始处理元素(%s)...' %(path_name))
        result = 0
        if self.running_event.isSet() :
            #print('线程：开始检测线程暂停标志...')
            self.suspend_event.wait()       # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
            #print('线程：检测线程暂停标志结束。')
            if not self.running_event.isSet() :
                log.get_logger().info('线程：暂停完成后检测有提前退出信号，退出处理0。')
                return -1
            result = self.impl_obj.deal_with(path_name, is_dir)
            if result == 1 :
                self.current += 1
                if self.item_count > 0 :
                    percent = int(self.current * 100 / self.item_count)
                    self.notify(path_name, Percent=percent)
                    #print('线程：处理有效元素(%s)完成，进度(%d%%)。' %(path_name, percent))
        else :
            log.get_logger().info('线程：收到提前退出信号，退出处理1。')
            return -1
        return 0

    def run(self):
        canceled = False        #提前结束标志
        s_info = ''
        #print('线程开始运行...')
        log.get_logger().info('线程：工作根目录=%s.' %self.root_dir)
        finish_flag = 0
        s_info = '重要：开始pre_build处理，根目录=(%s)...' %(self.root_dir)
        self.notify(s_info)
        if self.impl_obj.pre_build(self.root_dir) :
            s_info = '重要：开始统计需要处理的元素...'
            log.get_logger().info(s_info)
            self.notify(s_info, Percent=Task_Impl_Base.CIRCLE_PROGRESS)
            self.current = 0
            self.calc_item_count()
            s_info = '重要：根目录(%s)下共有(%d)个元素需要处理。' %(self.root_dir, self.item_count)
            log.get_logger().info(s_info)
            self.notify(s_info, Percent=Task_Impl_Base.CIRCLE_PROGRESS)
            info = ''
            percent = 0
            s_info = '开始处理根目录(%s)...' %(self.root_dir)
            log.get_logger().info(s_info)
            self.notify(s_info, Percent=percent)
            if self.item_count > 0 :
                for p, ds, fs in os.walk(self.root_dir, topdown=self.top_to_down) :
                    for d in ds :
                        path_name = os.path.join(p, d)
                        if self.deal_one_item(path_name, True) == -1 :
                            canceled = True
                            break
                    if canceled :
                        log.get_logger().info('线程：收到提前退出信号，退出处理（目录）1。')
                        break                
                    for f in fs :
                        path_name = os.path.join(p, f)
                        if self.deal_one_item(path_name, False) == -1 :
                            canceled = True
                            break
                    if canceled :
                        log.get_logger().info('线程：收到提前退出信号，退出处理（文件）2。')
                        break
                if not canceled :
                    if self.deal_one_item(self.root_dir, True) == -1 :
                        canceled = True
                log.get_logger().info('线程：元素循环处理结束。')
                if self.current < self.item_count :
                    info = '重要：元素处理提前结束，共有(%d)，已处理(%d)。' %(self.item_count, self.current)
                    if self.item_count > 0 :
                        percent = int(self.current * 100 / self.item_count)
                    else :
                        percent = 100
                else :
                    info = '重要：元素处理全部完成，共有(%d)，处理(%d)。' %(self.item_count, self.current)
                    percent = 100
                finish_flag = -1 if canceled else 1
            else :   #没有元素需要处理
                info = '重要：根目录下没有元素需要处理。'
                percent = 100
                log.get_logger().info(info)
            #info = '元素处理全部完成。'    
            self.notify(info, Percent=percent)
            self.impl_obj.post_build(self.root_dir, canceled)
        else :
            info = '异常：impl对象pre_build失败，线程提前结束。' 
            log.get_logger().info(info)
            self.notify(info, Percent=100)
        self.finish_notify(self.notify_obj, finish_flag)
        return
        
    def pause(self):
        log.get_logger().info('收到暂停通知，suspend_event开始复位...')
        self.suspend_event.clear()     # 设置为False, 让线程阻塞
        log.get_logger().info('suspend_event复位完成。')
    def resume(self):
        log.get_logger().info('收到恢复通知，suspend_event开始置位...')
        self.suspend_event.set()    # 设置为True, 让线程停止阻塞
        log.get_logger().info('suspend_event置位完成。')
    def cancel(self):
        log.get_logger().info('收到取消通知，两个标志位处理...')
        self.suspend_event.set()       # 将线程从暂停状态恢复, 如何已经暂停的话
        self.running_event.clear()        # 设置为False    
        log.get_logger().info('两个标志位处理完成。')
        return
