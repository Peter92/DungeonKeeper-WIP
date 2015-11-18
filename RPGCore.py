from __future__ import division
import math
import copy

class MovementError(Exception):
    """Custom movement exceptions."""
    CoordinateIndexError = 'coordinate index out of range'
    CoordinateTypeError = 'value given must be tuple or list of {} values'
    CoordinateValueError = 'values given must be numbers'
    
def split_decimal_part(n):
    """Split the input into its integral part and its decimal part.
    Returns as string to avoid an error with -0.x.

    Parameters:
        n (str/int/float): Integer to convert.

    >>> split_decimal_part('15.35321')
    ('15', '35321')
    """
    n = str(n)
    try:
        integral, decimal = n.split('.')
    except ValueError:
        return int(n), 0
    else:
        return str(integral) if integral else '0', str(decimal) if decimal else '0'
        
class Movement(object):
    """This was built to allow large coordinates to be stored without
    causing any floating point precision errors.
    It is faster than the decimal module, especially with processing
    large amounts of small movements.

    It works by breaking down the coordinates into 'blocks', where each
    new block is the squared amount of the previous one.
    The method is very similar to the base number system, in which a
    block size of 10 will split 235.9 into [5.9, 3, 2].

    A large block size is faster than a small one, though the precision
    will be worse. At 16 digits, Python can't store any more decimals,
    so definitely keep it under that.
    """

    BLOCK_SIZE = 65535
    COORDINATES = range(3)

    def __init__(self, start=(0, 0, 0), block_size=None, raw=False):
        """Convert the starting coordinates into the format accepted
        by the class.

        >>> m = Movement('15',
        ...              '-31564.99933425584842',
        ...              '1699446367870005.2')
        >>> m.raw
        [[15.0], [-31564.99933425585], [38640.2, 17514, 2485, 6]]

        >>> print m
        (15.0, -31564.9993343, 1699446367870005.2)
        """
        
        
        if isinstance(start, Movement):
            self = copy.deepcopy(start)
            return
        
        self.len = len(start)
        self.TypeError = MovementError.CoordinateTypeError.format(self.len)
        if self.len == 1:
            self.TypeError = self.TypeError[:-1]

        #Set a new block size if needed
        if block_size is not None:
            self.BLOCK_SIZE = block_size

        if raw == True:
            self.raw = start
        
        else:
            #Store the initial coordinates
            self.raw = [self.calculate(*split_decimal_part(i))
                               for i in map(str, start)]
    def copy(self):
        return copy.deepcopy(self)

    def __repr__(self):
        """This needs improving, currently it just converts back to
        the absolute coordinates."""
        return 'Movement({})'.format(self._convert_to_world())


    def __str__(self):
        """Print the absolute coordinates."""
        return str(tuple(self._convert_to_world())).replace("'", "")

    def __len__(self):
        return self.len

    def __add__(self, x):
        """Add a tuple to the location.
        
        >>> m = Movement(0, 0, 0)
        >>> print m + (5, 5, 5)
        (5.0, 5.0, 5.0)
        >>> print m
        (0.0, 0.0, 0.0)
        >>> m += (-1.75, 50, '1.19504')
        >>> print m
        (-1.75, 50.0, 1.19504)
        """
        self_copy = copy.deepcopy(self)
        try:
            self_copy.move(x)
        except TypeError:
            raise TypeError(self.TypeError)
        except ValueError:
            raise ValueError(MovementError.CoordinateValueError)
        return self_copy
    __radd__ = __add__
    
    
    def __sub__(self, x):
        """Subtract a tuple to the location.
        
        >>> m = Movement(0, 0, 0)
        >>> print m - (5, 5, 5)
        (-5.0, -5.0, -5.0)
        >>> print m
        (0.0, 0.0, 0.0)
        >>> m -= (-1.75, 50, '1.19504')
        >>> print m
        (1.75, -50.0, -1.19504)
        """
        self_copy = copy.deepcopy(self)
        try:
            self_copy.move(['-' + i if '-' not in i else i[1:] for i in map(str, x)])
        except TypeError:
            raise TypeError(self.TypeError)
        except ValueError:
            raise ValueError(MovementError.CoordinateValueError)
        return self_copy
    
    
    def __rsub__(self, x):
        """Subtract the location from a tuple.
        
        >>> m = Movement(0, 0, 0)
        >>> print (5, 5, 5) - m 
        (5.0, 5.0, 5.0)
        >>> print m
        (0.0, 0.0, 0.0)
        >>> (-1.75, 50, '1.19504') -= m
        Traceback (most recent call last):
        SyntaxError: can't assign to literal
        """
        if len(x) != self.len:
            raise TypeError(self.TypeError)
        start = Movement(x)
        start.move(self.raw)
        return start
    
    
    def __mul__(self, x):
        """Multiply the location by a tuple or integer.
        
        >>> m = Movement(10, -10, 0)
        >>> print m * (5, 5, 5)
        (50.0, -50.0, 0.0)
        >>> print m
        (10.0, -10.0, 0.0)
        >>> m *= (-1.75, 50, '1.19504')
        >>> print m
        (-17.5, -500.0, 0.0)
        >>> print 1000.123 * m 
        (-17502.1525, -500061.5, 0.0)
        """
        self_copy = copy.deepcopy(self)
        try:
            #Multiply by a single value
            x = int(x) if str(x).isdigit() else float(x)
            self_copy.raw = [[block * x for block in coordinate] 
                                    for coordinate in self.raw]
        except TypeError:
            
            #Multiply by a list/tuple
            try:
                if len(x) != self.len:
                    raise TypeError(self.TypeError)
                    
                x = [n if str(n).isdigit() else float(n) for n in x]
                self_copy.raw = [[block * mult for block in coordinate]
                                        for coordinate, mult 
                                        in zip(self.raw, x)]
            except ValueError:
                raise ValueError(MovementError.CoordinateValueError)
                
        except ValueError:
            raise ValueError(MovementError.CoordinateValueError)
        self_copy._overflow()
        
        return self_copy
    __rmul__ = __mul__


    def __getitem__(self, i):
        """Return an absolute value for X, Y or Z.

        Parameters:
            i (int): Index of coordinate.
        """
        try:
            return self._convert_to_world()[i]
        except IndexError:
            raise IndexError(MovementError.CoordinateIndexError)


    def __setitem__(self, i, n):
        """Set an absolute value for X, Y or Z.

        Parameters:
            i (int): Index of coordinate.

            n (int/float): New value to set.
        """
        n = str(n)
        try:
            self.raw[i] = self.calculate(*split_decimal_part(n))
        except IndexError:
            MovementError.index_error_coordinate()


    def calculate(self, amount, decimal=0):
        """Convert the coordinate into a block.

        Parameters:
            amount (int/str): Total value without any decimals.

            decimal (int, optional): The decimal value as an integer
                without the leading '0.'.

        >>> Movement().calculate(128)
        [128.0]
        >>> Movement().calculate(128, 5176)
        [128.5176]
        >>> Movement().calculate(4294836224)
        [65534.0, 65534]
        >>> Movement().calculate(4294836225)
        """
        negative_zero = amount == '-0'
        amount = int(amount)
        if negative_zero:
            multiplier = -1
        else:
            multiplier = -1 if int(amount) < 0 else 1#int(math.copysign(1, amount))
        amount *= multiplier

        coordinate = []
        while amount >= self.BLOCK_SIZE:
            amount, remainder = divmod(amount, self.BLOCK_SIZE)
            coordinate.append(int(remainder * multiplier))
        coordinate.append(int(amount * multiplier))

        decimal = float('0.{}'.format(decimal))
        coordinate[0] += decimal * multiplier

        return coordinate


    def _move(self, direction, amount, final_run=False):
        """Add the coordinate to a block.

        Parameters:
            direction (int): Represents X, Y, or Z as a number.

            amount (int/float): Amount to add or subtract from the
            coordinate.

        >>> m = Movement(135, 426.42, -1499941.5002)
        >>> print m
        (135.0, 426.42, -1499941.5002)

        >>> m.move(100, -5133.100532, 5)
        >>> print m
        (235.0, -4706.680532, -1499936.5002)
        """
        
        if isinstance(amount, list):
            new_blocks = amount
        else:
            #Fix floats going into exponentials
            if 'e' in str(amount):
                amount = int(round(amount))
            new_blocks = self.calculate(*split_decimal_part(amount))
        
        #Calculate new blocks and add to old ones
        for i, amount in enumerate(new_blocks):
            try:
                self.raw[direction][i] += amount
            except IndexError:
                self.raw[direction].append(amount)
        
    def _overflow(self):
        
        for i, coordinate in enumerate(self.raw):
        
            #Overflow large values into next block
            overflow = 0
            for j, amount in enumerate(coordinate):
                amount += overflow
                negative = math.copysign(1, amount)
                overflow, remainder = [n * negative for n in divmod(abs(amount), self.BLOCK_SIZE)]
                if j:
                    remainder = int(remainder)
                self.raw[i][j] = remainder
            
            #Add extra blocks
            while overflow:
                negative = math.copysign(1, overflow)
                overflow, remainder = [n * negative for n in divmod(abs(overflow), self.BLOCK_SIZE)]
                self.raw[i].append(int(remainder))

    def move(self, location, max_speed=None, reverse=False):
        """Update the coordinates with a new relative location."""
        
        if len(location) != self.len:
            raise TypeError(self.TypeError)
        
        #Stop total speed going over max value
        if max_speed is not None:
            total_speed = pow(sum(pow(i, 2) for i in location), 0.5)
            if total_speed > max_speed:
                multiplier = max_speed / total_speed
                location = tuple(amount * multiplier for amount in location)
        
        for i, amount in enumerate(location):
            if amount:
                if reverse:
                    amount = -amount
                self._move(i, amount)
        self._overflow()
        return self

    def _convert_to_world(self):
        """Convert the blocks into absolute coordinates as a string."""

        #Convert coordinates back to numbers, without using floats
        coordinates = [sum(int(amount) * pow(self.BLOCK_SIZE, i)
                           for i, amount in enumerate(coordinate))
                       for coordinate in self.raw]

        #Add the decimal points as strings
        coordinates = ['{}.{}'.format(coord, str(location[0]).split('.')[1])
                       for coord, location in zip(coordinates, self.raw)]

        #Fix for numbers between -1 and 0
        for i, location in enumerate(self.raw):
            if len(location) == 1 and (-1 < location[0] < 0):
                coordinates[i] = '-' + coordinates[i]
                
        return coordinates
