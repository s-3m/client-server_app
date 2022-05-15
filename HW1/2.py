def info_word(values: tuple):
    for i in values:
        i = eval(f'b"{i}"')
        print(f'{type(i)} - {i}. Length - {len(i)}')


words_for_check = ('class', 'function', 'method')
info_word(words_for_check)
