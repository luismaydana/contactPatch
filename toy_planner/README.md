# contactPatch "little Toy" Planner

This is a small version of the battery planner in ContactPatch. 

We know that a lap has 10 segments and that the battery starts full with 3 units. In each segment, we can deploy one unit to save time or not deploy one, recovering one in braking segments (3,6,8) up to maximun of 3

Our goal is to find the shortest lap time and the deployment plan that achieves it. 

## How it works? Well...

As we know: "Brute Force" simulates...

all 1024 possible plans and keeps the fastest(achievable)

"Dynamic Programming" stores the maximun remaining time that is in "dp[s][battery]", starting at segment "s" with that battery charge, and fills the table(backward) from segment 10 to 1.

The program then reconstructs the plan, simulates it (to check the predicted time), and compares both methods(plans and times).

Since it is a brute force we have 100% confidence of finding the optimal. After all we covered all the cases, didn't we?

Now going to the interesting part:

## How the DP calculates each cell

So, let's denote "Row 11" like the row where we cross the finish line. Every value in that row is zero because there  are no segments left.

For each segment before this one, the program compared 2 choices.

1. If deployment is skipped.

Then the battery gains one unit when the segment is, indeed, a braking segment and the battery is below capacity.
Remaining sacing is:


```python
skip = dp[s+1 ][next_battery]
```

2. If deployment is chose.n

Then the battery must have at least one unit to spend.
The sacing is the current gain of the segment + the best remaining saving with one fewer battery unit:


```python
deploy = gain[s] +dp[s+1][battery-1]
```

The cell keeps the larger saving. 

Filling the table backward means that  the next row is already computed(before is needed).

So...For example, at segment 10, the battery has only 1 unit, skipping saves 0. Deploying saves 45 hundredths of a second, so `dp[10][1]=45`.

After filling the table, `dp[1][3]=245`.

Starting with full battery therefore saves 2.45 seconds:

```text
90.00-2.45 = 87.55 seconds
```


## Reconstructing

The program starts at segment 1 with 3 battery units. 
At each segment 

We check whether deploying achieves the saving stored in the current cell. 

If it does, the segment is added to the plan and one battery unit is spent. 
If it doesn't, deployment is skipped and the battery recharges when applicable.

| Segment | Action | Battery after | Time saved |
|---|---|---:|---:|
| Start | Full battery | 3 | — |
| 1 | Deploy | 2 | 0.30 s |
| 2 | Deploy | 1 | 0.50 s |
| 3 | Recharge | 2 | 0 |
| 4 | Deploy | 1 | 0.20 s |
| 5 | Deploy | 0 | 0.40 s |
| 6 | Recharge | 1 | 0 |
| 7 | Deploy | 0 | 0.60 s |
| 8 | Recharge | 1 | 0 |
| 9 | Skip | 1 | 0 |
| 10 | Deploy | 0 | 0.45 s |

## Running the program

Requirements:

Python 3(no external libraries). Run this command from the repository root:

```bash
python toy_planner/toy_planner.py
```

## Output


```text
brute force  1024  plans tried: 456 achievable
Best lap:  87.55 s
Deploy  in segments:  [1, 2, 4, 5, 7, 10]

Dynamic programming:  44 cells
Best lap:  87.55 s
Deploy  in segments:  [1, 2, 4, 5, 7, 10]

Same  answer
3 BIGGEST GAINS: 88.45 s
```

Both methos found a lap time of **87.55 seconds**, deploying in segments **1,2,4,5,7 and 10**. Brute force checks **1024 plans** and **456 feasible plans**, while the DP table contains **44cells** and the 3-biggest-gains rule gives **88.45 seconds**

## Why are 44 cells enough?

We have 11 rows, including the finish row, and 4 battery levels per row(The unused row 0 is empty).

So... 2 plans that reach the same segmentwith the same battery charge have the same options.

The DP just calculates the best remaining saving for that state once and reuses it.


| Method | Time, worst case  | Memory |
|---|---:|---:|
| DP | $O(n(C+1))$ | $O(n(C+1))$ |
| Brute Force | $`O(n^2\,2^n)`$ | $`O(n\,2^n)`$ |


we can clearly see why DP is better  espcially in longer tracks and more secions of deployment,  we have linear complexity over exponential, so for bigger things, DP is WAY better

## who wrote this?
All in this "toy_planner" is written by me "Luis Maydana" 

I wrote all the code myself on November 21(2026),  I didn't use AI to write it, edit, debug any part of it.
I also wrote the whole README. The problem statement and  input  valeus were provided in advance, as well as a separate answer key for the result