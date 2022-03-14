ParallelaPy
===========


    Parallelize any Python function and capture the return.

## Must Read

The below examples will get you started using the library. 

At it's simplest, the library takes a function and an iterator, executes them in parallel, and returns an object containing the function returns and any exceptions that occurred. Passed tasks will be in `my_obj.passed_tasks` while failed tasks will be in `my_obj.failed_tasks`:

```python
def square_it(number):
    """Square a given number"""

    y = number ** 2
    return y

i = [1,2,3,4,'a']

# The arguments 'function' and 'iterable' are mandatory; you may call them by name or use them positionally
squares = RunParallel(function=square_it, iterable=i)

f = squares.execute()

# Note here that we are capturing the data as the return f from squares.execute()
for t in f.passed_tasks:
    print(f"{t.function_name} : {t.iter_id} : {t.return_data}")
# Returns:
>> square_it : 3 : 9
>> square_it : 1 : 1
>> square_it : 2 : 4
>> square_it : 4 : 16

for t in f.failed_tasks:
    print(f"{t.function_name} : {t.iter_id} : {t.failure_data}")
# Returns:
>> square_it : a : unsupported operand type(s) for ** or pow(): 'str' and 'int'
```

By default, only functions that raised Exceptions or otherwise failed to complete are considered failed. The user may specify that any function that returns `False` should also be considered a failure

```python
def is_even(number):
    """Return true if even"""

    if number % 2 == 0:
        return True
    else:
        return False
   
i = [1,2,3,4,'a']

# The arguments 'function' and 'iterable' are mandatory; you may call them by name or use them positionally
evns = RunParallel(is_even, i)

# Specify fail_on_false=True to mark any function that returns False as a failure
even_chk = evns.execute(fail_on_false=True)

# Note here that in contrast to above, we are capturing the data that has been updated in the RunParallel object evns. We could also capture the same data from even_chk as we did in Example #1. even_chk is created as a reference to the object evns, so they are in fact the same object
for t in evns.passed_tasks:
    print(f"{t.function_name} : {t.iter_id} : {t.return_data}")
# Returns:
>> is_even : 2 : True
>> is_even : 4 : True
        
for t in evns.failed_tasks:
    print(f"{t.function_name} : {t.iter_id} : {t.failure_data}")
# Returns:
>> is_even : 1 : Function returned False
>> is_even : 3 : Function returned False
>> is_even : a : not all arguments converted during string formatting
```

 The library is also capable of handling functions with additional inputs to the target function:

```python
def double_it(number, username, say_hello=False):
    """Take a number and return its double. Add some prints to demonstrate opt args"""
    
    if say_hello is True:
        print(f"Hello, {username}. Let's double {number}")
    
    y = number * 2
    return y

i = [1,2,3,4,'a']

# Order will always be: function to run, iterable, fct positional arg(s), fct named arg(s) ...
dbl_it = RunParallel(double_it, i, "John", say_hello=True)

# ... unless called with ALL function inputs named, in which case order does not matter
dbl_it = RunParallel(username="John", say_hello=True, function=double_it, iterable=i)

dbls = dbl_it.execute()

# These print statements return from inside the function double_it as it executes
>> Hello, John. Let's double 1
>> Hello, John. Let's double 2
>> Hello, John. Let's double 3
>> Hello, John. Let's double 4
>> Hello, John. Let's double a

for d in dbl_it.passed_tasks:
     print(f"{d.function_name} : {d.iter_id} : {d.return_data}")     
# Returns (note that order has changed):
>> double_it : 1 : 2
>> double_it : a : aa
>> double_it : 3 : 6
>> double_it : 2 : 4
>> double_it : 4 : 8
        
for d in dbl_it.failed_tasks:
     print(f"{d.function_name} : {d.iter_id} : {d.failure_data}")
# Since Python can multiply a string, there are no Exceptions raised and this is empty
```

In addition to accessing the data as a list of returned `TaskResult` objects, the library provides methods to access the data as lists:

```python
def square_cube_it(number):
    """Square and cube a given number, return a tuple with the values"""

    y = number ** 2
    z = number ** 3
    return (y, z)

square_cube = RunParallel(function=square_cube_it, iterable=i)

# No need to assign the output, as the square cube object itself will contain the data
square_cube.execute()

print(square_cube.all_pass_ids())
>> [3, 2, 1, 4]

print(square_cube.all_pass_data())
>> [(9, 27), (4, 8), (1, 1), (16, 64)]

print(square_cube.all_fail_ids())
>> ['a', 'b']

print(square_cube.all_fail_data())
>> [TypeError("unsupported operand type(s) for ** or pow(): 'str' and 'int'"), TypeError("unsupported operand type(s) for ** or pow(): 'str' and 'int'")]
# ^ This is not a TypeError, rather it captured the TypeErrors triggered by attempting to square the strings 'a' and 'b'
```



## New Objects

The library adds two objects, a `RunParallel` object that takes a function and an iterator, and when give the `.execute()` method, will return a `TaskResult` object.

### TaskResult

Is returned on completion of the parallelized execution. Has the properties:

```python
self.function  			# Ref to the Python function that was executed
self.function_name 		# Function name as a string
self.iter_id 			# The iterator value that was passed to the function
self.task_complete		# Boolean that is True if task completed without Exceptions
self.failure_data		# Contains Exception details if the task failed, or None if it succeeded
self.return_data		# Contains the return value from the function
```

### RunParallel

Sets up the needed information, executes the function, and then is updated with the return data upon completion. It contains a number of properties:

```python
self.function  			# Ref to the Python function that will be executed
self.function_name 		# Function name as a string
self.iterable 			# The iterable (list, dict, generator, etc) that will be executed in paral
self.max_parallel		# Max number of threads to use
self.opt_args			# Any positional arguments (other than iterable) accepted by the target function
self.opt_kwargs 		# Any named arguments (other than iterable) accepted by the target function

# Stores the completion status
self.execution_started  # Sets to True when the function execution has started
self.execution_complete # Set to True when all functions have completed (or have caught Exceptions)
self.passed_tasks		# A list of TaskResult objects that passed
self.failed_tasks		# A list of TaskResult objects that failed
```

The object also contains a number of methods:

#### execute(self, fail_on_false=False)

Starts the execution of the given function and iterables. By default, only Execptions or functions that fail to complete are considered failures. If `fail_on_false=True` then any function that returns `False` will also by marked as a failed task

```python
# Function and iterable must be defined prior to .execute being called()
squares = RunParallel(function=square_it, iterable=i)

# Start execution with no special rules
f = squares.execute()

# Start execution with a rule stating that if the function return is False, the Task should count as a failed_task even if no Exceptions are raised
f = squares.execute(fail_on_false=True)
```

#### all_pass_data(self)

Get a list of all returns from functions that passed

```python
f.all_pass_data()
>> [9, 1, 4, 16]
```

#### all_pass_ids(self)

Get a list of all iterator elements that passed

```python
f.all_pass_ids()
>> [3, 1, 2, 4]
```

#### all_fail_data(self)

Get a list of all failure types

```python
f.all_fail_data()
>> [TypeError("unsupported operand type(s) for ** or pow(): 'str' and 'int'"), TypeError("unsupported operand type(s) for ** or pow(): 'str' and 'int'")]
```

#### all_fail_ids(self)

Get a list of all iterator elements that failed

```python
f.all_fail_ids()
>> ['a', 'b']
```



Note
====

This project has been set up using PyScaffold 4.1.4. For details and usage
information on PyScaffold see https://pyscaffold.org/.
