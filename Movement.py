class Movement(object):
    """This was built to allow large coordinates to be stored without causing any floating point precision errors.
    It is faster than the decimal module, especially with processing large amounts of small movements.
    
    It works by breaking down the coordinates into 'blocks', where each new block is the squared amount of the previous one.
    The method is very similar to the base number system, in which a block size of 10 will split 235.9 into [5.9, 3, 2].
    
    A large block size is faster than a small one, though the precision will be worse. At 16 digits, Python can't store any more decimals, so definitely keep it under that.
    """
    
    BLOCK_SIZE = 65535
    COORDINATES = range(3)
    
    def __init__(self, x=0, y=0, z=0, block_size=None):
        """Convert the starting coordinates into the format accepted by the class.
        
        >>> m = Movement('15', '-31564.99933425584842', '1699446367870005.2464800004')
        >>> m.player_loc
        [[15.0], [-31564.99933425585], [38640.2464800004, 17514, 2485, 6]]
        
        >>> print m
        (15.0, -31564.9993343, 1699446367870005.24648)
        """
        
        #Set a new block size if needed
        if block_size is not None:
            self.BLOCK_SIZE = block_size
            
        #Store the initial coordinates
        self.player_loc = [self.calculate(self._get_integer(i), self._get_decimal(i)) for i in map(str, (x, y, z))]
    
    
    def __repr__(self):
        """This needs improving, currently it just converts back to the absolute coordinates."""
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
            self.player_loc[i] = self.calculate(self._get_integer(n), self._get_decimal(n))
        except IndexError:
            MovementError.index_error_coordinate()
            
            
    @classmethod
    def _get_integer(self, n):
        """Convert the input to an integer.
        
        Parameters:
            n (str): Integer to convert.
            
        >>> Movement._get_integer('15.35321')
        15
        """
        return int(n) if '.' not in n else int(n.split('.')[0])
    
    
    @classmethod
    def _get_decimal(self, n):
        """Get the decimal number from the input.
        
        Parameters:
            n (str): Decimal to convert.
            
        >>> Movement._get_decimal('15.35321')
        35321
        """
        return 0 if '.' not in n else int(n.split('.')[1])
    
    
    def calculate(self, amount, decimal=0):
        """Convert the coordinate into a block.
        
        Parameters:
            amount (int/str): Total value without any decimals.
            
            decimal (int, optional): The decimal value as an integer without the leading '0.'.
        
        >>> Movement().calculate(128)
        [128.0]
        >>> Movement().calculate(128, 5176)
        [128.5176]
        >>> Movement().calculate(4294836224)
        [65534.0, 65534]
        >>> Movement().calculate(4294836225)
        [0.0, 0, 1]
        """
        coordinate = []
        amount = int(amount)
        negative = amount < 0
        multiplier = int('-1'[not negative:])
        
        if negative:
            amount *= -1
        
        while amount > self.BLOCK_SIZE - 1:
            remainder = amount % self.BLOCK_SIZE
            amount = (amount - remainder) / self.BLOCK_SIZE
            coordinate.append(int(remainder * multiplier))
        coordinate.append(int(amount * multiplier))
        
        decimal = float('0.' + str(int(decimal))) * int('-1'[not coordinate[0] < 0:])
        coordinate[0] += decimal
        
        return coordinate


    def _move(self, direction, amount, final_run=False):
        """Add the coordinate to a block.
        
        Parameters:
            direction (int): Represents X, Y, or Z as a number.
            
            amount (int or float): Amount to add or subtract from the coordinate.
        """
        
        #Fix to keep decimals on large numbers
        if not final_run and amount > self.BLOCK_SIZE:
            decimal = self.player_loc[direction][0] % 1
            if '.' in str(amount):
                decimal += float('0.' + str(amount).split('.')[1])
            self.player_loc[direction][0] = int(self.player_loc[direction][0]) + int(amount)
        else:
            self.player_loc[direction][0] += amount
        
        #Recalculate and add blocks if needed
        i = 0
        while i < len(self.player_loc[direction]):
            stop = True
            while not -self.BLOCK_SIZE < self.player_loc[direction][i] < self.BLOCK_SIZE:
                stop = False
                
                remainder = self.player_loc[direction][i] % self.BLOCK_SIZE
                new_addition = int(self.player_loc[direction][i] - remainder) / self.BLOCK_SIZE
                if i:
                    remainder = int(remainder)
                self.player_loc[direction][i] = remainder
                
                try:
                    self.player_loc[direction][i + 1] += new_addition
                except IndexError:
                    self.player_loc[direction].append(new_addition)
            
            #Break execution if higher blocks are not edited
            if stop:
                break
                
            i += 1
        
        #Add the final decimals if a large number was input
        try:
            self._move(direction, decimal, final_run=True)
        except UnboundLocalError:
            pass
        

    def move(self, x, y, z):
        """Update the coordinates with a new relative location."""
        for i, amount in enumerate((x, y, z)):
            if amount:
                self._move(i, amount)
    
    
    def _convert_to_world(self):
        """Convert the blocks into absolute coordinates in string format."""
        absolute_coordinates = [sum(int(amount) * pow(self.BLOCK_SIZE, i) for i, amount in enumerate(coordinate)) for coordinate in self.player_loc]
        absolute_coordinates = ['{}.{}'.format(absolute_coordinates[i], str(float(self.player_loc[i][0])).split('.')[1]) for i in self.COORDINATES]
        for i in self.COORDINATES:
            if len(self.player_loc[i]) == 1 and str(self.player_loc[i][0]).startswith('-0.'):
                absolute_coordinates[i] = '-' + absolute_coordinates[i]
        return absolute_coordinates
            
            
class MovementError(Exception):
    """Custom movement exceptions."""
    @classmethod
    def index_error_coordinate(self):
        raise MovementError('coordinate index out of range')
