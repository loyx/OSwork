import random
from collections import deque
from copy import copy
from abc import ABC, abstractmethod

from task import Task


class Schglorithm(ABC):

    def __init__(self, time, resume_time, waiteQueue, readQueue, finishQueue,
                 initTime, task_num, std_args, ls_rate, io_rate, total_num,
                 cpu_record):

        # Schedule 传入参数
        self.time = time
        self.resume_time = resume_time
        self.waiteQueue = waiteQueue
        self.readQueue = readQueue
        self.finishQueue = finishQueue
        self.initTime = initTime
        self.task_num = task_num
        self.ls_rate = ls_rate
        self.io_rate = io_rate
        self.__std_long, self.__std_short = std_args
        self.total_num = total_num
        self.cpu_record = cpu_record

        # algorithm 传出参数
        self.long_task_num = 0
        self.short_task_num = 0

    ''' 这样写是不想重构太多 '''
    def return_parameters(self):
        return self.long_task_num, self.short_task_num

    @ abstractmethod
    def sim(self):
        """ 不同调度算法 """

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

    def _get_resume_time(self):
        return random.randint(int(self.__std_short/3),
                              int(self.__std_short/2)) + self.time.get_time()

    def _resume_task(self):
        if len(self.resume_time) > 0 and self.resume_time[0] <= self.time.get_time():
            assert len(self.waiteQueue) != 0
            resume_task = self.waiteQueue.popleft()
            resume_task.unblock()
            self.readQueue.append(resume_task)
            del self.resume_time[0]

    def _debug(self):
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


class FCFS(Schglorithm):
    def sim(self):
        while True:
            if self.time.get_time() > 800:
                self._debug()
            self.start_one_task()

            self._resume_task()
            if len(self.readQueue) != 0:
                run_task = self.readQueue.popleft()
                # print("run_task:", run_task.id)
                # if run_task.id == 4:
                #     print(run_task.context)
                task_state = run_task.propel_task()

                if task_state > 0:
                    run_task.block()
                    self.waiteQueue.append(run_task)
                    self.resume_time.append(self._get_resume_time())
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


class RR(Schglorithm):

    def __init__(self, *args, quantum=1):
        super().__init__(*args)
        self.quantum = quantum

    def sim(self):
        assert len(self.finishQueue) == 0
        t_scale = self.quantum
        time_limit = t_scale

        while True:
            self.start_one_task()

            self._resume_task()

            if len(self.readQueue) != 0:

                run_task = self.readQueue.popleft()
                task_state = run_task.propel_task()
                time_limit -= 1

                if task_state > 0:
                    time_limit = t_scale
                    run_task.block()
                    self.waiteQueue.append(run_task)
                    self.resume_time.append(self._get_resume_time())
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


class MF(Schglorithm):

    def __init__(self, *args, quantums):
        super().__init__(*args)
        self.quantums = quantums

    def sim(self):
        quantums = list(self.quantums)
        queue_num = len(quantums)
        time_limit = copy(quantums)
        while True:
            if self.time.get_time() > 800:
                self._debug()
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
                        self.resume_time.append(self._get_resume_time())
                    elif task_state == -1:
                        time_limit = copy(quantums)
                        run_task.finish()
                        self.finishQueue.append(run_task)
                    else:
                        if time_limit[qi] == 0:
                            self.readQueue[(qi + 1) % queue_num].append(run_task)
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
                return
