import random
# from collections import defaultdict

# 计算总权重
def calculate_total_weight(current_state, states, category_distances, distance_weights):
    total_weight = 0
    current_class = None
    for cls, state_list in states.items():
        if current_state in state_list:
            current_class = cls
            break
    if current_class is None:
        raise ValueError("Current state not found in any class.")
    
    for cls, state_list in states.items():
        distance = category_distances[current_class][cls]
        weight = distance_weights.get(distance, 0)
        total_weight += weight * len(state_list)
    return total_weight

# 计算每个目标状态的概率
def calculate_probabilities(current_state, states, category_distances, distance_weights):
    probabilities = {}
    current_class = None
    for cls, state_list in states.items():
        if current_state in state_list:
            current_class = cls
            break
    if current_class is None:
        raise ValueError("Current state not found in any class.")
    
    total_weight = calculate_total_weight(current_state, states, category_distances, distance_weights)
    
    for cls, state_list in states.items():
        distance = category_distances[current_class][cls]
        weight = distance_weights.get(distance, 0)
        class_weight = weight * len(state_list)
        for state in state_list:
            if state != current_state:
                probabilities[state] = class_weight / total_weight
    return probabilities

# 实现状态扰动
def perturb_state(current_state):
    # 定义状态和类别
    states = {
        'Positive': [
        "admiration",
        "amusement",
        "approval",
        "caring",
        "curiosity",
        "desire",
        "excitement",
        "gratitude",
        "joy",
        "love",
        "optimism",
        "pride",
        "realization",
        "relief"
    ],
        'Neutral': ['neutral'],
        'Ambiguous': [
        "confusion",
        "disappointment",
        "nervousness"
    ],
        'Negative': [
        "anger",
        "annoyance",
        "disapproval",
        "disgust",
        "embarrassment",
        "fear",
        "sadness",
        "remorse"
    ]
    }

    # 定义类别之间的距离
    category_distances = {
        'Positive': {'Positive': 0, 'Neutral': 1, 'Ambiguous': 2, 'Negative': 3},
        'Neutral': {'Positive': 1, 'Neutral': 0, 'Ambiguous': 1, 'Negative': 2},
        'Ambiguous': {'Positive': 2, 'Neutral': 1, 'Ambiguous': 0, 'Negative': 1},
        'Negative': {'Positive': 3, 'Neutral': 2, 'Ambiguous': 1, 'Negative': 0}
    }

    # 定义距离权重
    distance_weights = {
        0: 10,  # 同类状态
        1: 5,  # 相邻类别
        2: 2,  # 相隔一个类别
        3: 1   # 相隔两个类别
    }

    probabilities = calculate_probabilities(current_state, states, category_distances, distance_weights)
    next_state = random.choices(list(probabilities.keys()), weights=list(probabilities.values()), k=1)[0]
    return next_state

