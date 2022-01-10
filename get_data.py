import numpy as np
import pandas as pd

def get_data():
    data = pd.read_excel(r'C:\Users\Lenovo\Desktop\data.xlsx')

    serve=data['s'] #s 表示服务时长
    deadline=data['d'] #d 表示不能超过的最晚时间
    begin_time=data['e'] #e 表示服务必须开始的时间
    x = data['x']
    y = data['y']
    care_cost =200 #表示医护人员的价格
    punishument = data['w']  #表示每个人的超时成本
    l=data['l']#过了这个时间要罚钱了
    d = createDistanceMatrix(x,y)

    time_cost =d  #表示两点之间的时间成本
    travel_cost = d #表示两点之间的旅行成本

    return serve,deadline,time_cost,travel_cost,care_cost,punishument,l,begin_time

def createDistanceMatrix(x, y):
    n = len(x)
    d = np.zeros((n,n))
    for i in range(n):
        for j in range(i+1,n):
            p1 = np.array([x[i], y[i]])
            p2 = np.array([x[j], y[j]])
            d[i,j] = d[j,i] = int(round(np.linalg.norm(p1-p2)))
    return d
