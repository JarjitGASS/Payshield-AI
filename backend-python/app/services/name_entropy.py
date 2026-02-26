import math

#name entropy pake Shannon Entropy buat calculate random string
def name_entropy(name: str) -> float:
    name = name.replace(" ", "").lower()

    if not name:
        return 0.0
    
    freq = {}
    for char in name:
        freq[char] = freq.get(char, 0) + 1


    #shannon entropy = sum of -p(xi) * log2(p(xi))
    #p(xi) -> probability of xi -> xi here is character cuz name
    entropy = 0.0
    length = len(name)
    for count in freq.values():
        p = count / length
        entropy += (-p) * math.log2(p)
    #normalize with log2
    max_entropy = math.log2(length) if length > 1 else 1
    norm_entropy = entropy / max_entropy if max_entropy else 0.0
    return round(norm_entropy, 3)
