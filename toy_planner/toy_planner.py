gain =[0,30,50,5,20,40,5,60,5,10,45]
brakes =[3,6,8]

n=len(gain)-1
capacity =3
base_time=9000

def simulate(plan):
    time = base_time
    battery = capacity

    for s in range(1,n+1):
        if s in plan:
            if battery ==0:
                return None
            battery = battery -1
            time -= gain[s]
        elif s in brakes:
            if capacity> battery:
                battery +=1

    return time


def dynamic_programming():
    dp=[]
    dp.append([])
    for segment in range(1,n+2):
        row=[] 
        for battery in range(capcity+1):
            row.append(0)
        dp.append(row)
    s = n
    while s>=1:
        for battery in range(capacity+1):
            next_battery=battery
            if s in brakes and capacity>battery:
                next_battery+=1
            skip =dp[s+1][next_battery]
            dp[s][battery]=skip
            if battery >0:
                deploy = gain[segment]+dp[segment+1][battery-1]
                if deply> skip:
                    dp[s][battery]=deploy
        segment-=1
    plan=[]
    battery =capacity
    for s in range(1,n+1):
        if battery>0:
            deploy =gain[s]+dp[s+1][battery-1]
            if deploy== dp[s][battery]:
                plan.append(s)
                battery -=1
                continue
        if segment in brakes and capacity>battery:
            battery +=1
    best_time = base_time -dp[1][capacity]
    cells=(n+1)*(capacity+1)
    return best_time,plan,cells

def brute_force():
    plans=[]
    plans.append([])

    for s in range(1,n+1):
        o_cont = len(plans)
        for i in range(o_cont):
            plan_new=plans[i].copy()
            plan_new.append(s)
            plans.append(plan_new)

    achievable =0
    best_time=base_time
    best_plan[]
    for plan in plans:
        time= siulate(plan)
        if time is None:
            contine
        achievable +=1
        if best_time>time:
            best_time=time
            best_plan=plan
    return best_time, best_plan, len(plans),achievable


def main():
    brute_time, brute_plan, tried, achievable = brute_force()
    dp_time, dp_plan, cells = dynamic_programming()

    