import math
import random
import itertools
import pandas as pd
import time

def euclid(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

# 3-opt (safe, fast)
def three_opt(tour_points):
    n = len(tour_points)
    improved = True
    iterations = 0
    while improved and iterations < 100:
        improved = False
        iterations += 1
        for i in range(n - 5):
            for j in range(i + 2, n - 3):
                a, b, c, d = tour_points[i], tour_points[i+1], tour_points[j], tour_points[j+1]
                if euclid(a, c) + euclid(b, d) < euclid(a, b) + euclid(c, d) - 1e-6:
                    tour_points[i+1:j+1] = tour_points[i+1:j+1][::-1]
                    improved = True
                    break
            if improved: break
    return tour_points

# Cook's Ruler seed
def cooks_ruler_seed(points, tolerance):
    n = len(points)
    if n < 2: return list(range(n))
    
    # Farthest pair
    si = ei = 0
    max_d = 0
    for i, j in itertools.combinations(range(n), 2):
        d = euclid(points[i], points[j])
        if d > max_d:
            max_d, si, ei = d, i, j
    
    # Projection
    S, E = points[si], points[ei]
    vec_SE = (E[0]-S[0], E[1]-S[1])
    D2 = vec_SE[0]**2 + vec_SE[1]**2 or 1
    proj = {}
    for i, pt in enumerate(points):
        vec_SP = (pt[0]-S[0], pt[1]-S[1])
        proj[i] = (vec_SP[0]*vec_SE[0] + vec_SP[1]*vec_SE[1]) / D2
    
    min_p = min(proj.values())
    span = max(proj.values()) - min_p or 1
    lx = lambda i: (proj[i] - min_p) / span
    
    step = 1.0 / n
    tour = [si]
    visited = {si}
    cur = si
    log_x = 0.0
    
    while log_x < 1.0:
        log_x = min(log_x + step, 1.0)
        cand = [i for i in range(n) if i not in visited and abs(lx(i) - log_x) <= step * tolerance]
        if cand:
            cand.sort(key=lambda i: euclid(points[cur], points[i]))
            for i in cand:
                tour.append(i)
                visited.add(i)
                cur = i
    
    if ei not in visited:
        tour.append(ei)
    
    # Ensure tour has exactly n cities
    while len(tour) < n:
        remaining = [i for i in range(n) if i not in tour]
        next_i = min(remaining, key=lambda i: euclid(points[cur], points[i]))
        tour.append(next_i)
        cur = next_i
    
    return tour

# GA — 
def ga_cooks_ruler(points, pop_size=60, generations=120):
    n = len(points)
    
    # Seed with Cook's Ruler
    population = []
    for _ in range(pop_size):
        tour = cooks_ruler_seed(points, random.uniform(0.8, 2.2))
        if len(tour) != n:
            tour = tour + [i for i in range(n) if i not in tour][:n-len(tour)]
        population.append(tour)
    
    for gen in range(generations):
        # Fitness
        fitness = []
        for tour in population:
            length = sum(euclid(points[tour[i]], points[tour[(i+1)%n]]) for i in range(n))
            fitness.append(length)
        
        # Elites
        elites = [x for _, x in sorted(zip(fitness, population))[:pop_size//5]]
        
        # Breed
        offspring = elites.copy()
        while len(offspring) < pop_size:
            p1, p2 = random.sample(elites, 2)
            start, end = sorted(random.sample(range(n), 2))
            child = p1[:]
            segment = p1[start:end]
            remaining = [x for x in p2 if x not in segment]
            child = remaining[:start] + segment + remaining[start:]
            # Mutation
            if random.random() < 0.1:
                i, j = random.sample(range(n), 2)
                child[i], child[j] = child[j], child[i]
            offspring.append(child)
        
        population = offspring
        
        if gen % 40 == 0:
            print(f"Gen {gen}: {min(fitness):,.0f}")
    
    # Final best + 3-opt
    best_tour = min(population, key=lambda t: sum(euclid(points[t[i]], points[t[(i+1)%n]]) for i in range(n)))
    best_points = [points[i] for i in best_tour] + [points[best_tour[0]]]
    best_points = three_opt(best_points)
    final_len = sum(euclid(best_points[i], best_points[i+1]) for i in range(len(best_points)-1))
    return final_len

# Load data
print("Loading data...")
points_100 = pd.read_csv("us_cities_100.csv")[['lat','lon']].values.tolist()
points_1000 = pd.read_csv("us-cities-top-1k.csv")[['lat','lon']].values.tolist()
points_clustered = pd.read_csv("US_Accidents_March23.csv", usecols=['Start_Lat','Start_Lng']).dropna().drop_duplicates().head(1000).values.tolist()

datasets = [
    (points_100, "100 US Cities"),
    (points_1000, "1,000 Nationwide US Cities"),
    (points_clustered, "1,000 Clustered (March 2023)")
]

for points, name in datasets:
    print(f"\n=== {name} ===")
    start = time.time()
    length = ga_cooks_ruler(points)
    print(f"Cook's Ruler + GA + 3-opt: {length:,.0f} miles")
    print(f"Time: {time.time()-start:.1f}s")
