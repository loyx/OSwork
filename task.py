import random


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
