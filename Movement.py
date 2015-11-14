from __future__ import division
import math

def split_decimal_part(n):
    """Split the input into its integral part and its decimal part.

    Parameters:
        n (str/int/float): Integer to convert.

    >>> Movement.split_decimal_part('15.35321')
    (15, 35321)
    """
    n = str(n)
    try:
        integral, decimal = n.split('.')
    except ValueError:
        return int(n), 0
    else:
        return int(integral) if integral else 0, int(decimal) if decimal else 0
            
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

    def __init__(self, x=0, y=0, z=0, block_size=None):
        """Convert the starting coordinates into the format accepted
        by the class.

        >>> m = Movement('15',
        ...              '-31564.99933425584842',
        ...              '1699446367870005.2')
        >>> m.player_loc
        [[15.0], [-31564.99933425585], [38640.2, 17514, 2485, 6]]

        >>> print m
        (15.0, -31564.9993343, 1699446367870005.2)
        """

        #Set a new block size if needed
        if block_size is not None:
            self.BLOCK_SIZE = block_size

        #Store the initial coordinates
        self.player_loc = [self.calculate(*split_decimal_part(i))
                           for i in map(str, (x, y, z))]


    def __repr__(self):
        """This needs improving, currently it just converts back to
        the absolute coordinates."""
        return 'Movement({}, {}, {})'.format(*self._convert_to_world())


    def __str__(self):
        """Print the absolute coordinates."""
        return str(tuple(self._convert_to_world())).replace("'", "")


    def __getitem__(self, i):
        """Return an absolute value for X, Y or Z.

        Parameters:
            i (int): Index of coordinate.
        """
        try:
            return self._convert_to_world()[i]
        except IndexError:
            MovementError.index_error_coordinate()


    def __setitem__(self, i, n):
        """Set an absolute value for X, Y or Z.

        Parameters:
            i (int): Index of coordinate.

            n (int/float): New value to set.
        """
        n = str(n)
        try:
            self.player_loc[i] = self.calculate(*split_decimal_part(n))
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
        [0.0, 0, 1]
        """
        amount = int(amount)
        multiplier = int(math.copysign(1, amount))
        amount *= multiplier

        coordinate = []
        while amount >= self.BLOCK_SIZE - 1:
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
        
        #Fix floats going into exponentials
        if 'e' in str(amount):
            amount = int(round(cur_speed))
        axis = self.player_loc[direction]
        
        #Calculate new blocks and add to old ones
        for i, amount in enumerate(self.calculate(*split_decimal_part(amount))):
            try:
                axis[i] += amount
            except IndexError:
                axis.append(amount)
        
        #Overflow large values into next block
        overflow = 0
        for i, amount in enumerate(axis):
            amount += overflow
            negative = math.copysign(1, amount)
            overflow, remainder = [n * negative for n in divmod(abs(amount), self.BLOCK_SIZE)]
            self.player_loc[direction][i] = remainder
        
        #Add extra blocks
        while overflow:
            negative = math.copysign(1, overflow)
            overflow, remainder = [n * negative for n in divmod(abs(overflow), self.BLOCK_SIZE)]
            self.player_loc[direction].append(remainder)


    def move(self, x, y, z, max_speed=None):
        """Update the coordinates with a new relative location."""
        movement = (x, y, z)
        
        #Stop total speed going over max value
        if max_speed is not None:
            total_speed = pow(sum(pow(i, 2) for i in movement), 0.5)
            if total_speed > max_speed:
                multiplier = max_speed / total_speed
                movement = tuple(amount * multiplier for amount in movement)
        
        for i, amount in enumerate(movement):
            if amount:
                self._move(i, amount)

        return self

    def _convert_to_world(self):
        """Convert the blocks into absolute coordinates as a string."""

        #Convert coordinates back to numbers, without using floats
        coordinates = [sum(int(amount) * pow(self.BLOCK_SIZE, i)
                           for i, amount in enumerate(coordinate))
                       for coordinate in self.player_loc]

        #Add the decimal points as strings
        coordinates = ['{}.{}'.format(coord, str(location[0]).split('.')[1])
                       for coord, location in zip(coordinates, self.player_loc)]

        #Fix for numbers between -1 and 0
        for i, location in enumerate(self.player_loc):
            if len(location) == 1 and (-1 < location[0] < 0):
                coordinates[i] = '-' + coordinates[i]
                
        return coordinates


class MovementError(Exception):
    """Custom movement exceptions."""
    @classmethod
    def index_error_coordinate(self):
        raise MovementError('coordinate index out of range')
