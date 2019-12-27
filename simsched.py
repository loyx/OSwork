from matplotlib import pyplot as plt
import random
# from random import random
from collections import deque
from copy import copy


class Timer:

    def __init__(self, time=0):
        self.__curr_time = time

    def get_time(self):
        return self.__curr_time

    def add_time(self):
        self.__curr_time += 1

    def set_time(self, time):
        self.__curr_time = time


class Task:
    ID = 1

    def __init__(self, length, io_rate=(0,), time=None):
        assert length > 0
        self.id = Task.ID
        Task.ID += 1
        self.time = time
        self.length = length

        io_times = []
        for rate in io_rate:
            io_times.append(int(rate*length))
        context = [0] * length
        rlen = len(io_rate)
        for i in range(rlen):
            for j in range(length):
                if context[j] == 0 and random.random() < io_rate[i] and io_times[i] > 0:
                    context[j] = i + 1
                    io_times[i] -= 1
        self.context = context

        self.start_time = self.time.get_time()
        self.finish_time = -1

        self.next_point = 0
        self.io_tag = 0
        self.finish_tag = 0

        self.last_run_time = self.start_time
        self.waitTime = 0

    def __del__(self):
        Task.ID -= 1

    def summary(self):
        if self.finish_time == -1:
            print("this task is not finish!")
            return -1
        return self.start_time, self.finish_time, self.finish_time - self.start_time, self.context, self.waitTime

    def propel_task(self):
        if self.next_point == self.length:
            self.finish_tag = 1
            return -1  # indicate the task has finished

        if self.finish_tag == 1 or self.io_tag == 1:
            return -1

        self.next_point += 1

        gap = self.time.get_time() - self.last_run_time
        if gap <= 1:
            self.waitTime += 1
        self.last_run_time = self.time.get_time()

        return self.context[self.next_point - 1]

    def block(self):
        assert self.io_tag == 0
        self.io_tag = 1

    def unblock(self):
        assert self.io_tag == 1
        self.io_tag = 0

    def finish(self):
        assert self.finish_time == -1
        self.finish_time = self.time.get_time()


class Schedule:
    __fact = 0.25
    __std_long = int(50 * __fact)
    __std_short = int(20 * __fact)
    __io_time = [int(__std_short / 10), int(__std_short / 5), int(__std_long / 5)]

    def __init__(self, task_num=15, ls_rate=0.4, io_rate=(0.1,), fun='fcfs', seed=None, concurrent=1):
        if seed is not None:
            random.seed(seed)
        self.quantum = None
        self.time = Timer()

        # io_rate = (0,)
        # if iotype == 0:
        #     io_rate = (0.05,)
        # elif iotype == 1:
        #     io_rate = (0.1,)
        self.io_rate = io_rate
        self.task_num = task_num
        self.long_task_num = 0
        self.short_task_num = 0
        self.ls_rate = ls_rate
        self.resume_time = []

        rng = int(concurrent*self.__std_short*5)+2
        # if concurrent:
        #     rng = self.__std_short
        # else:
        #     rng = self.__std_short*5
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

        self.fun = fun
        self.cpu_record = []
        self.total_num = self.task_num

    def simulate(self, quantum=6, quantums=(4, 6, 15)):
        if self.fun == 'fcfs':
            self.FCFS()
        elif self.fun == 'rr':
            self.quantum = quantum
            self.RR(quantum)
        else:
            self.quantum = quantums
            self.readQueue = [deque() for i in range(len(quantums))]
            self.MF(quantums)

    def start_one_task(self):
        if isinstance(self.readQueue, list):
            assert len(self.readQueue) > 0
            queue = self.readQueue[0]
        else:
            queue = self.readQueue
        assert isinstance(queue, deque)

        if self.task_num != 0 and self.time.get_time() >= self.initTime[0]:
            self.task_num -= 1
            rng = int(self.__std_short / 4)
            if random.random() > self.ls_rate:
                task = Task(self.__std_long+random.randint(-rng, rng), self.io_rate, self.time)
                self.long_task_num += 1
            else:
                task = Task(self.__std_short+random.randint(-rng, rng), self.io_rate, self.time)
                self.short_task_num += 1
            queue.append(task)
            del self.initTime[0]

    def FCFS(self):
        while True:
            if self.time.get_time() > 800:
                self.__debug()
            # self.__debug()
            self.start_one_task()

            if len(self.resume_time) > 0 and self.resume_time[0] <= self.time.get_time():
                assert len(self.waiteQueue) != 0
                resume_task = self.waiteQueue.popleft()
                resume_task.unblock()
                self.readQueue.append(resume_task)
                del self.resume_time[0]

            if len(self.readQueue) != 0:
                run_task = self.readQueue.popleft()
                # print("run_task:", run_task.id)
                # if run_task.id == 4:
                #     print(run_task.context)
                task_state = run_task.propel_task()

                if task_state > 0:
                    run_task.block()
                    self.waiteQueue.append(run_task)
                    self.resume_time.append(self.__get_resume_time())
                elif task_state == -1:
                    run_task.finish()
                    self.finishQueue.append(run_task)
                else:
                    self.readQueue.appendleft(run_task)

                self.cpu_record.append(run_task.id)
            else:
                self.cpu_record.append(0)

            self.time.add_time()

            if self.total_num == len(self.finishQueue):
                assert len(self.waiteQueue) + len(self.readQueue) == 0
                return

    def RR(self, quantum):
        assert len(self.finishQueue) == 0
        t_scale = quantum
        time_limit = t_scale

        while True:
            self.start_one_task()

            if len(self.resume_time) > 0 and self.resume_time[0] <= self.time.get_time():
                assert len(self.waiteQueue) != 0
                resume_task = self.waiteQueue.popleft()
                resume_task.unblock()
                self.readQueue.append(resume_task)
                del self.resume_time[0]

            if len(self.readQueue) != 0:

                run_task = self.readQueue.popleft()
                task_state = run_task.propel_task()
                time_limit -= 1

                if task_state > 0:
                    time_limit = t_scale
                    run_task.block()
                    self.waiteQueue.append(run_task)
                    self.resume_time.append(self.__get_resume_time())
                elif task_state == -1:
                    time_limit = t_scale
                    run_task.finish()
                    self.finishQueue.append(run_task)
                else:
                    if time_limit == 0:
                        self.readQueue.append(run_task)
                        time_limit = t_scale
                    else:
                        self.readQueue.appendleft(run_task)

                self.cpu_record.append(run_task.id)
            else:
                self.cpu_record.append(0)

            self.time.add_time()

            if self.total_num == len(self.finishQueue):
                assert len(self.waiteQueue) + len(self.readQueue) == 0
                return

    def MF(self, quantums):
        quantums = list(quantums)
        queue_num = len(quantums)
        time_limit = copy(quantums)
        while True:
            if self.time.get_time() > 800:
                self.__debug()
            self.start_one_task()

            if len(self.resume_time) > 0 and self.resume_time[0] <= self.time.get_time():
                assert len(self.waiteQueue) != 0
                priority, resume_task = self.waiteQueue.popleft()
                resume_task.unblock()
                priority -= 1
                if priority < 0:
                    priority = 0
                self.readQueue[priority].append(resume_task)
                del self.resume_time[0]

            fg = True
            for qi in range(queue_num):
                if len(self.readQueue[qi]):

                    run_task = self.readQueue[qi].popleft()
                    task_state = run_task.propel_task()
                    time_limit[qi] -= 1

                    if task_state > 0:
                        time_limit = copy(quantums)
                        run_task.block()
                        self.waiteQueue.append((qi, run_task))
                        self.resume_time.append(self.__get_resume_time())
                    elif task_state == -1:
                        time_limit = copy(quantums)
                        run_task.finish()
                        self.finishQueue.append(run_task)
                    else:
                        if time_limit[qi] == 0:
                            self.readQueue[(qi+1) % queue_num].append(run_task)
                            time_limit = copy(quantums)
                        else:
                            self.readQueue[qi].appendleft(run_task)

                    self.cpu_record.append(run_task.id)
                    fg = False
                    break

            if fg:
                self.cpu_record.append(0)

            self.time.add_time()

            if self.total_num == len(self.finishQueue):
                # assert len(self.waiteQueue) + len(self.readQueue) == 0
                return

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
        return self.total_num/total, time1, time2

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

    def __get_resume_time(self):
        return random.randint(int(self.__std_short/3), int(self.__std_short/2)) + self.time.get_time()

    def __debug(self):
        if isinstance(self.readQueue, deque):
            print("readQueue:", end='[')
            for x in self.readQueue:
                print(x.id, end=',')
        else:
            cnt = 0
            for q in self.readQueue:
                print("readQueue %d:" % cnt, end='[')
                for x in q:
                    print(x.id, end=',')
                cnt += 1
        print("]\nwaitQueue:", end='[')
        for x in self.waiteQueue:
            print(x.id, end=',')
        print("]\nfinishQueue:", end='[')
        for x in self.finishQueue:
            print(x.id, end=',')
        print(']')
        print("______________________")
