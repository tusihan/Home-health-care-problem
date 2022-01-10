from gurobipy import *
import numpy as np
from get_data import get_data

import time

m=99999999999999
serve,deadline,time_cost,travel_cost,care_cost,punishument,l,begin_time = get_data()

n=27
care=6
model = Model("model")
model.setParam("OutputFlag", 0)
model.setParam('Timelimit', 7200)
starttime = time.time()
x={}
z={}
s={}
#添加决策变量
for i in range(n):
    for k in range(care):
        for j in range(n):
            if(i != j):
                name = 'x_' + str(i) + '_' + str(j) + '_' + str(k)
                x[i,j,k] = model.addVar(0
                                        , 1
                                        , vtype= GRB.BINARY
                                        , name= name) 
for i in range(n):
    for k in range(care):
        name = 's_' + str(i) + '_' + str(k)
        s[i,k] = model.addVar(0
                            , 3000
                            , vtype= GRB.CONTINUOUS
                            , name= name)  #定义访问时间为连续变量

for i in range(n):
    z[i] = model.addVar(-999999
                        ,9999999 
                        , vtype= GRB.CONTINUOUS
                        , name= name)  #定义访问时间为连续变量

#添加约束条件
#每个用户都要被访问到
for i in range(1, n - 1):
    lhs = LinExpr(0) 
    for k in range(care):
        for j in range(1, n): #这里用n还是n-1可能有点问题
            if(i != j):
                lhs.addTerms(1, x[i,j,k])  
    model.addConstr(lhs == 1, name= 'customer_visit_' + str(i)) 

    
#形成路径
for k in range(care):
    for h in range(1, n - 1):
        expr1 = LinExpr(0)
        expr2 = LinExpr(0)
        for i in range(n):
            if (h != i):
                expr1.addTerms(1, x[i,h,k])

        for j in range(n):
            if (h != j):
                expr2.addTerms(1, x[h,j,k])

        model.addConstr(expr1 == expr2, name= 'flow_conservation_' + str(i))
        expr1.clear()
        expr2.clear()

#每辆车都要出发
for k in range(care):
    lhs = LinExpr(0) 
    for j in range(n-1):
        if(j != 0):
            lhs.addTerms(1, x[0,j,k])  
    model.addConstr(lhs == 1, name= 'vehicle_depart_' + str(k))
    
#每辆车都要开回来
for k in range(care):
    lhs1 = LinExpr(0)
    lhs2 = LinExpr(0)
    for j in range(1,n-1):
        lhs1.addTerms(1, x[j, n-1, k])
        lhs2.addTerms(1, x[0,j,k])
    model.addConstr(lhs1 == lhs2, name= 'vehicle_enter_' + str(k))

for k in range(care):
    for i in range(n):
        for j in range(n):
            if(i != j):
                model.addConstr(s[i,k] + time_cost[i,j] + serve[i] - m + m * x[i,j,k] <= s[j,k] , name= 'time_windows_%s%s%s'%(i,j,k))


#ready_time
for i in range(n):
    for k in range(care):
        model.addConstr(s[i,k]>=begin_time[i], name= 'ready_time')
        model.addConstr(s[i,k] <= deadline[i], name= 'due_time')


#添加目标函数
obj1 = LinExpr(0)   
for i in range(n):
    for k in range(care):
        for j in range(n):
            if(i != j):
                obj1.addTerms(travel_cost[i,j], x[i,j,k])  

model.setObjective(200*quicksum(x[0,j,k] for j in range(1,n-1)for k in range(care))+obj1, GRB.MINIMIZE)  


model.update();
iter=0
z_value={}
# ================================================benders========================================
while True:
    model.optimize()

    iter = iter+1
    z_value[0] = sum(model.getAttr('x',z).values())
    print("z_value[0]",z_value[0])
    print(model.getObjective().getValue())
    x_solve = model.getAttr('x',x)
    s_solve = model.getAttr('x',s)
    for k in range(care):
        for i in range(n):
            for j in range(n):
                if i!=j:
                    if int(x_solve[i,j,k])>0:
                        print((i,j,k))
    
    # 子问题
    list_duals=[]
    sub_value=[]
    for i in range(n):
        sub=Model("sub")
        sub.setParam("OutputFlag", 0)
        pun={}
        #添加决策变量
        for k in range(care):
            name1 = 'pun_' + str(i) + '_' + str(k)
            pun[i,k] = sub.addVar(0
                                , 30000
                                , vtype= GRB.CONTINUOUS
                                , name= name1)  #定义访问时间为连续变量
            
        #添加约束条件
    #时间状态
        for k in range(care):
            sub.addConstr(pun[i,k]>=(s_solve[i,k]-l[i]))
            sub.addConstr(pun[i,k]>=0)


        #添加目标函数
        obj = LinExpr(0)  
        for k in range(care):
            obj.addTerms(punishument[i], pun[i,k])

        sub.setObjective(obj, GRB.MINIMIZE)   
    
        sub.update()
        sub.optimize()
        if sub.status == GRB.Status.INFEASIBLE:
            print('Optimization was stopped with status %d' % sub.status)
        # do IIS, find infeasible constraints
            sub.computeIIS()
            for c in sub.getConstrs():
                if c.IISConstr:
                    print('%s' % c.constrName)

        list_dual = sub.getAttr('Pi')
        list_duals.append(list_dual)
        sub_value.append(sub.getObjective().getValue())


    z_value[iter] = sum(sub_value)
    print('z[%s]'%(iter),z_value[iter])
    

    
    if z_value[0]<0:
        midvar=[] 
        for i in range(n):
            midvar1=[]
            for k in range(care):
                midvar1.append(s[i,k]-l[i])
            midvar.append(midvar1)
                
        midvar2=[]
        for i in range(0,n):
            midvar3=0
            for k in range(care):
                midvar3=midvar3+list_duals[i][k]*midvar[i][k] 
            midvar2.append(midvar3)

        for i in range(n):
            model.addConstr(midvar2[i]<=z[i],name='punish%s'%str(i))
        
        model.setObjective(200*quicksum(x[0,j,k] for j in range(1,n-1)for k in range(care))+obj1+quicksum(z[h]for h in range(n)), GRB.MINIMIZE)  
        # model.setObjective(1200+obj1+quicksum(z[h]for h in range(n)), GRB.MINIMIZE)  

        model.update()
    else:
        break


model.update();
model.optimize()
endtime = time.time()
print("所用时间",endtime-starttime,"s")
obj_res = model.getObjective().getValue()
print(obj_res)
                  
x_solve = model.getAttr('x',x)
for k in range(care):
    for i in range(n):
        for j in range(n):
            if i!=j:
                if int(x_solve[i,j,k])>0:
                    print((i,j,k))