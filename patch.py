with open('ui/aces_monitor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
for line in lines:
    if '    p3_select = mo.ui.dropdown(options=_opts, value=0' in line:
        out.append('    _default = list(_opts.keys())[0]\n')
        out.append('    p3_select = mo.ui.dropdown(options=_opts, value=_default, label="Select session")\n')
    else:
        out.append(line)

with open('ui/aces_monitor.py', 'w', encoding='utf-8') as f:
    f.writelines(out)
print('Done')
