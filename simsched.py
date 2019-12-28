from collections import deque
from matplotlib import pyplot as plt

import schalgorithm
from task import *


class Schedule:
    __fact = 0.25
    __std_long = int(50 * __fact)
    __std_short = int(20 * __fact)
    __io_time = [int(__std_short / 10), int(__std_short / 5), int(__std_long / 5)]

    def __init__(self, task_num=15, ls_rate=0.4, io_rate=(0.1,), fun='fcfs',
                 seed=None, concurrent=1, **kwargs):
        if seed is not None:
            random.seed(seed)
        self.quantum = None
        self.time = Timer()

        self.io_rate = io_rate
        self.task_num = task_num

        # delegate parameter
        self.long_task_num = 0
        self.short_task_num = 0

        self.ls_rate = ls_rate
        self.resume_time = []

        rng = int(concurrent*self.__std_short*5)+2
        init_time = [0]
        temp = [i for i in range(1, rng)]
        while len(temp) < task_num:
            temp.append(temp[0])
        tl = random.sample(temp, task_num - 1)
        tl.sort()
        init_time.extend(tl)

        assert len(init_time) == task_num
        # print(init_time, task_num)
        self.initTime = init_time

        self.readQueue = deque()
        self.waiteQueue = deque()  # 扩展多级阻塞队列
        self.finishQueue = deque()
        self.cpu_record = []
        self.total_num = self.task_num
        self.fun = fun
        self.algorithm = self.get_algorithm(kwargs)

    def get_algorithm(self, kwargs):
        assert isinstance(kwargs, dict)
        args = [self.time, self.resume_time, self.waiteQueue, self.readQueue, self.finishQueue,
                self.initTime, self.task_num, (self.__std_long, self.__std_short), self.ls_rate, self.io_rate,
                self.total_num, self.cpu_record]
        if self.fun == 'fcfs':
            return schalgorithm.FCFS(*args)
        if self.fun == 'rr':
            print(kwargs['quantum'])
            return schalgorithm.RR(*args, quantum=kwargs['quantum'])
        if self.fun == 'mf':
            quantums = kwargs['quantums']
            args[3] = [deque() for _ in range(len(quantums))]
            return schalgorithm.MF(*args, quantums=quantums)

    '''delegate sim'''
    def simulate(self):
        self.algorithm.sim()
        self.long_task_num, self.short_task_num = self.algorithm.return_parameters()

    def result(self):
        time1 = 0
        time2 = 0
        max_len = 0
        min_len = 0x3f3f3f
        total_len = 0
        for task in self.finishQueue:
            _, _, rtime, context, wtime = task.summary()
            # print(task.id, context)
            time1 += rtime
            time2 += wtime
            max_len = max(max_len, len(context))
            min_len = min(min_len, len(context))
            total_len += len(context)
        time1 = time1 / self.total_num
        time2 = time2 / self.total_num
        total = len(self.cpu_record)
        return self.total_num/total, time1, time2, max_len, min_len, total_len

    def show(self):
        if self.fun == 'fcfs':
            st = "先来先服务"
            print("本次仿真调度算法：" + st)
        elif self.fun == 'rr':
            st = "时间片轮转"
            print("本次仿真调度算法：" + st)
            print("时间片长：{}".format(self.quantum))
        else:
            st = "多级反馈队列"
            print("本次仿真调度算法：" + st)
            print("各就绪队列时间片长：{}".format(self.quantum))
        print("仿真情况：")
        print("作业总数：{}".format(self.total_num))
        print("长短作业数及比例：\n\t长作业：{}  比例：{}%\n\t短作业：{}  比例：{}%"
              .format(self.long_task_num, self.long_task_num/self.total_num*100,
                      self.short_task_num, self.short_task_num/self.total_num*100))

        _,  time1, time2, max_len, min_len, total_len = self.result()
        print("最长作业长：{}, 最短作业长：{}, 作业总长：{}, 作业平均长：{}"
              .format(max_len, min_len, total_len, total_len/self.total_num))

        print("作业IO比例：{}".format(self.io_rate[0]))
        print("作业详情示例：")
        task = self.finishQueue[random.randint(0, self.total_num-1)]
        # print(task.context)
        print("|", end='')
        for c in task.context:
            if c == 0:
                print("█", end='')
            else:
                print(" ", end='')
        print("|")
        total = len(self.cpu_record)
        use = 0
        for x in self.cpu_record:
            if x > 0:
                use += 1
        print("CPU总运行时间：{}\n\t空转时间：{}  比例：{}%\n\t运算时间：{}  比例：{}%"
              .format(total, total-use, (total-use)/total*100, use, use/total*100))
        print("吞吐量：%.2f" % (self.total_num/total))

        print("平均周转时间：{}\n平均等待时间：{}".format(time1, time2))

        # 绘制甘特图
        clist = ['b', 'g', 'r', 'c', 'm', 'y']
        gent = {}
        st = 0
        pre = -1
        i = 0
        self.cpu_record.append(-1)
        # print("cpu_record", self.cpu_record)
        for x in self.cpu_record:
            if x != pre:
                if pre > 0:
                    assert st != i
                    gent.setdefault(pre, []).append((st, i))
                pre = x
                st = i
            i += 1
        # print(gent)
        for i in range(self.total_num):
            sl = gent[i+1]
            for st, ed in sl:
                # print(st, ed)
                plt.barh(i+1, ed-st, left=st, facecolor=clist[i % 6])
                plt.text(st, i+1, "J%d" % (i+1))
        plt.ylabel("job NO.")
        plt.xlabel("CPU time")
        plt.show()
        return self.total_num/total, time1, time2
