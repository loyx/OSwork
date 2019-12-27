from matplotlib import pyplot as plt
import simsched

plt.rcParams['font.sans-serif'] = ['SimHei']


def test(fun, type=0, lens=50):
    task_num = 7
    ls_rate = 0.5
    seed = 1
    quantum = 10
    quantums = (5, 10, 20)
    io_rate = (0.1, )
    concurrent = 0
    x = [x/lens for x in range(lens)]
    y = [[], [], []]
    cnt = 0
    xstr = ''
    for io in range(0, lens):
        if type == 0:
            ls_rate = io/lens
            xstr = '长短作业比例'
        elif type == 1:
            io_rate = (io/lens,)
            xstr = '作业IO占比'
        elif type == 2:
            concurrent = io/lens
            xstr = '作业并发程度'
        print("当前比例：{}%".format(io/lens))
        y1 = 0
        y2 = 0
        y3 = 0
        for i in range(20):
            sim = simsched.Schedule(fun=fun, task_num=task_num,
                                    ls_rate=ls_rate, io_rate=io_rate,
                                    concurrent=1-concurrent)
            sim.simulate(quantum=quantum, quantums=quantums)
            t1, t2, t3 = sim.show()
            # t1, t2, t3 = sim.result()
            y1 += t1
            y2 += t2
            y3 += t3
            return
        y1 /= 5
        y2 /= 5
        y3 /= 5
        y[0].append(y1)
        y[1].append(y2)
        y[2].append(y3)
        cnt += 1
        print("进度：{}%".format(cnt/lens*100))
    plt.plot(x, y[1], x, y[2])
    plt.legend(['平均周转时间', '平均等待时间'])
    plt.xlabel(xstr)
    plt.title("调度算法："+fun)
    plt.show()
    return x, y[1], y[2]


if __name__ == '__main__':

    cx = []
    cy1 = []
    cy2 = []
    methods = ['fcfs', 'rr', 'mf']
    for i in methods:
        for j in range(3):
            tx, ty1, ty2 = test(i, j)
            cx.append(tx)
            cy1.append(ty1)
            cy2.append(ty2)

