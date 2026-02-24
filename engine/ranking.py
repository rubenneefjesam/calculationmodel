def update_top_list(lst, record, key, reverse=False, top_n=10):
    lst.append(record)
    lst.sort(key=lambda x: x[key], reverse=reverse)
    if len(lst) > top_n:
        lst.pop()