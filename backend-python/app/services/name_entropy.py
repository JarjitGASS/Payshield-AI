import math
import re

#name entropy pake Shannon Entropy buat calculate random string
def shannon_entropy(name: str) -> float:
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

def ngram_entropy(name: str, n: int = 2) -> float:
    name = name.replace(" ", "").lower()
    if len(name) < n:
        return 0.0
    
    ngrams = [name[i:i+n] for i in range(len(name)-n+1)]

    freq = {}

    for ng in ngrams:
        freq[ng] = freq.get(ng, 0) + 1
    
    entropy = 0.0

    total = len(ngrams)
    for count in freq.values():
        p = count / total
        entropy += (-p) * math.log2(p)
    max_entropy = math.log2(total) if total > 1 else 1
    return round(entropy / max_entropy if max_entropy else 0.0, 3)


def has_digits_or_symbols(name: str) -> bool:
    return bool(re.search(r'[^a-zA-Z ]', name))

def name_entropy(name: str) -> float:
    combined_entropy = (shannon_entropy(name) + ngram_entropy(name, n=2)) / 2
    return combined_entropy