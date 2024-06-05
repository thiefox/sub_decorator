import os

from datetime import datetime

from subtitle.sub_filer import sub_filer
from subtitle.srt_sub_event import srt_sub_event

class srt_sub_filer(sub_filer) :
    def __init__(self) :
        super().__init__()
        return
    def reindex(self) :
        i = 1 
        for e in self.events :
            assert(isinstance(e, srt_sub_event))
            e.set_index(i)
            i += 1
        return
    #重载函数
    def build(self) -> bool :
        MAX_SECONDS = 3
        t_begin = datetime.now()
        print('time={}, begin srt_sub_filer::build...'.format(t_begin.strftime('%H:%M:%S')))
        assert(len(self.events) == 0)
        print('srt_sub_filter load, 数据行={}...'.format(len(self.lines)))
        begin = 0
        while True :
            event = srt_sub_event.search_event(self.lines, begin, LAST_INDEX=-1)
            #print('build.search_event, begin={}, event={}'.format(begin, event.print_interval()))
            if event.raw_valid() :
                begin = event.inter.get_event_end()
                if event.build_txt() :
                    self.events.append(event)
                else :
                    if event.has_mt() :
                        print('异常：事件{}, 时间轴={} 编译字幕文本失败。'.format(event.get_index(), event.print_time_axis()))
                    else :
                        print('忽略：事件{}无文本。'.format(event.get_index()))
            else :
                print('异常：事件{}无效，退出。'.format(event.print()))
                break
        print('srt_sub_filtter load，line pos={}, 原始事件数量={}'.format(begin, len(self.events)))
        #索引一致性订正
        self.reindex()
        t_end = datetime.now()
        if (t_end - t_begin).seconds > MAX_SECONDS :
            print('异常：srt_sub_filer::build处理时间过长={}秒'.format((t_end - t_begin).seconds))
        return len(self.events) > 0
