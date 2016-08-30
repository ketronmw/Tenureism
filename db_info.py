campus_names = ['san_diego','riverside', 'irvine', 'los_angeles','santa_barbara',
            'merced','santa_cruz','san_francisco','berkeley','davis']

table_names = ['profs_list_unique']
N = [3,4,5,8,10]
for n in N:
    table_names.append('profs_list_over'+str(n))
    table_names.append('profs_list_under'+str(n))
