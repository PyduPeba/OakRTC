# core/action_context.py

context_vars = {}

def update_context(reader):
    try:
        x, y, z = reader.get_position()
        context_vars['$posx'] = x
        context_vars['$posy'] = y
        context_vars['$posz'] = z
        context_vars['$cap'] = reader.get_capacity()
        context_vars['$hp'] = reader.get_hp()
        context_vars['$mp'] = reader.get_mana()
    except:
        pass
