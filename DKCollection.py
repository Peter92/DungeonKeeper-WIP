def split_decimal_part(n):
    """Split the input into its integral part and its decimal part.
    Returns as string to avoid an error with -0.x.

    Parameters:
        n (str/int/float): Integer to convert.

    >>> split_decimal_part('15.35321')
    ('15', '35321')
    """
    n = str(n)
    negative = n.startswith('-')
    try:
        integral, decimal = n.split('.')
    except ValueError:
        return n, '0'
    else:
        if not integral and decimal and negative:
            decimal = '-' + decimal
        return str(integral) if integral else '0', str(decimal) if decimal else '0'
        

def quick_hash(x, y, offset=10):
    dx = hash(str(x // 2) + str(y))
    dy = hash(str((y * x) // 2))
    num = int(0.5 * (dx + dy) * (dx + dy + 1)) % (offset * 2) - offset
    return num

def split_num(n):
    return (int(n), remove_int(n))
    
def remove_int(n):
    if n > 0:
        return n % 1
    try:
        n_decimal = str(n).split('.')[1]
        return float('-0.' + n_decimal)
    except IndexError:
        return 0.0
