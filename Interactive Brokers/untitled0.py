def pickingNumbers(a):
    # Write your code here
    def get_count(array, a_dict, key):
        for i in range(a_dict[key]):
            array.append(key)

    counter = {}
    array = []
    for element in a:
        if element not in counter:
            counter[element] = 1
        else:
            counter[element] += 1

    max_appeareance = max(counter, key=counter.get)
    get_count(array, counter, max_appeareance)
    
    if (m_plus_one:= max_appeareance + 1) in counter:
        get_count(array, counter, m_plus_one)
    if (m_minus_one:= max_appeareance - 1) in counter:
        get_count(array, counter, m_minus_one)

    return len(array)
out = pickingNumbers([1, 2, 2, 3, 1, 2])
print(out)
# [4, 6, 5, 3, 3, 1]